/**
 * AlgoViz Pro - Main Visualization Engine
 *
 * This script handles algorithm visualization on HTML5 Canvas,
 * including animation controls, state management, and rendering.
 */

class AlgorithmVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        // State management
        this.steps = [];
        this.currentStepIndex = 0;
        this.isPlaying = false;
        this.animationSpeed = 500; // milliseconds between steps
        this.animationTimer = null;

        // Canvas dimensions
        this.width = this.canvas.width;
        this.height = this.canvas.height;
        this.padding = 40;

        // Colors
        this.colors = {
            default: '#3b82f6', // Blue
            comparing: '#f59e0b', // Orange
            swapped: '#ef4444', // Red
            sorted: '#10b981', // Green
            pivot: '#8b5cf6', // Purple
            found: '#10b981', // Green
            background: '#ffffff', // White
            text: '#1f2937' // Dark gray
        };

        // Initialize UI
        this.initializeUI();
    }

    initializeUI() {
        // Get UI elements
        this.algorithmSelect = document.getElementById('algorithm-select');
        this.arrayInput = document.getElementById('array-input');
        this.targetInput = document.getElementById('target-input');
        this.targetGroup = document.getElementById('target-group');

        this.executeBtn = document.getElementById('execute-btn');
        this.playBtn = document.getElementById('play-btn');
        this.pauseBtn = document.getElementById('pause-btn');
        this.stepBtn = document.getElementById('step-btn');
        this.resetBtn = document.getElementById('reset-btn');

        this.speedSlider = document.getElementById('speed-slider');
        this.speedValue = document.getElementById('speed-value');

        // Statistics elements
        this.comparisonsCount = document.getElementById('comparisons-count');
        this.swapsCount = document.getElementById('swaps-count');
        this.arraySize = document.getElementById('array-size');
        this.currentStep = document.getElementById('current-step');
        this.timeElapsed = document.getElementById('time-elapsed');
        this.statusMessage = document.getElementById('status-message');
        this.stepMessage = document.getElementById('step-message');

        this.errorArea = document.getElementById('error-area');
        this.errorMessage = document.getElementById('error-message');

        // Event listeners
        this.algorithmSelect.addEventListener('change', () => this.onAlgorithmChange());
        this.executeBtn.addEventListener('click', () => this.execute());
        this.playBtn.addEventListener('click', () => this.play());
        this.pauseBtn.addEventListener('click', () => this.pause());
        this.stepBtn.addEventListener('click', () => this.stepForward());
        this.resetBtn.addEventListener('click', () => this.reset());
        this.speedSlider.addEventListener('input', () => this.updateSpeed());

        // Initialize
        this.onAlgorithmChange();
        this.clearCanvas();
    }

    onAlgorithmChange() {
        const algo = this.algorithmSelect.value;

        // Show/hide target input for searching algorithms
        if (algo === 'binary' || algo === 'linear') {
            this.targetGroup.style.display = 'block';
        } else {
            this.targetGroup.style.display = 'none';
        }
    }

    async execute() {
        // Get input values
        const algo = this.algorithmSelect.value;
        const arrayStr = this.arrayInput.value.trim();

        // Validate input
        if (!arrayStr) {
            this.showError('Please enter an array');
            return;
        }

        // Parse array
        try {
            const array = arrayStr.split(',').map(x => parseInt(x.trim()));

            // Validate array elements
            if (array.some(isNaN)) {
                this.showError('Array must contain only integers');
                return;
            }

            if (array.length === 0) {
                this.showError('Array cannot be empty');
                return;
            }

            if (array.length > 50) {
                this.showError('Array too large (maximum 50 elements)');
                return;
            }

            this.hideError();

            // Update UI
            this.statusMessage.textContent = 'Executing...';
            this.executeBtn.disabled = true;

            // Execute algorithm
            await this.executeAlgorithm(algo, array);

        } catch (error) {
            this.showError(`Error: ${error.message}`);
            this.executeBtn.disabled = false;
        }
    }

    async executeAlgorithm(algo, array) {
        try {
            let url = `/algorithms/execute/${algo}/`;
            let body = { array: array };

            // Add target for searching algorithms
            if (algo === 'binary' || algo === 'linear') {
                const target = parseInt(this.targetInput.value);
                if (isNaN(target)) {
                    this.showError('Please enter a valid target value');
                    this.executeBtn.disabled = false;
                    return;
                }
                // For searching, we'll need to add target to the request
                // For now, we'll use the array parameter
                body.target = target;
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to execute algorithm');
            }

            const data = await response.json();

            // Store steps
            this.steps = data.steps;
            this.currentStepIndex = 0;

            // Update statistics
            this.arraySize.textContent = data.input_size;
            this.currentStep.textContent = `0 / ${this.steps.length}`;

            // Enable controls
            this.playBtn.disabled = false;
            this.stepBtn.disabled = false;
            this.resetBtn.disabled = false;
            this.executeBtn.disabled = false;

            // Show first step
            this.renderStep(0);
            this.statusMessage.textContent = 'Ready to visualize';

        } catch (error) {
            this.showError(error.message);
            this.executeBtn.disabled = false;
        }
    }

    play() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        this.playBtn.disabled = true;
        this.pauseBtn.disabled = false;
        this.stepBtn.disabled = true;
        this.statusMessage.textContent = 'Playing...';

        this.animate();
    }

    pause() {
        this.isPlaying = false;
        this.playBtn.disabled = false;
        this.pauseBtn.disabled = true;
        this.stepBtn.disabled = false;
        this.statusMessage.textContent = 'Paused';

        if (this.animationTimer) {
            clearTimeout(this.animationTimer);
            this.animationTimer = null;
        }
    }

    animate() {
        if (!this.isPlaying) return;

        if (this.currentStepIndex < this.steps.length - 1) {
            this.stepForward();
            this.animationTimer = setTimeout(() => this.animate(), this.animationSpeed);
        } else {
            this.pause();
            this.statusMessage.textContent = 'Complete';
        }
    }

    stepForward() {
        if (this.currentStepIndex < this.steps.length - 1) {
            this.currentStepIndex++;
            this.renderStep(this.currentStepIndex);
        }
    }

    reset() {
        this.pause();
        this.currentStepIndex = 0;
        this.renderStep(0);
        this.playBtn.disabled = false;
        this.stepBtn.disabled = false;
        this.statusMessage.textContent = 'Reset to beginning';
    }

    renderStep(index) {
        if (index < 0 || index >= this.steps.length) return;

        const step = this.steps[index];

        // Update step counter
        this.currentStep.textContent = `${index + 1} / ${this.steps.length}`;

        // Update statistics
        if (step.comparisons !== undefined) {
            this.comparisonsCount.textContent = step.comparisons;
        }
        if (step.swaps !== undefined) {
            this.swapsCount.textContent = step.swaps;
        }
        if (step.time_ms !== undefined) {
            this.timeElapsed.textContent = `${step.time_ms.toFixed(2)} ms`;
        }

        // Update message
        if (step.message) {
            this.stepMessage.textContent = step.message;
        }

        // Render visualization
        this.clearCanvas();
        this.drawArray(step);
    }

    drawArray(step) {
        const array = step.array;
        if (!array || array.length === 0) return;

        const maxValue = Math.max(...array);
        const minValue = Math.min(...array);
        const range = maxValue - minValue || 1;

        // Calculate bar dimensions
        const availableWidth = this.width - (2 * this.padding);
        const availableHeight = this.height - (2 * this.padding);
        const barWidth = availableWidth / array.length;
        const barSpacing = 2;

        // Draw each bar
        array.forEach((value, index) => {
            const barHeight = ((value - minValue) / range) * availableHeight;
            const x = this.padding + (index * barWidth);
            const y = this.height - this.padding - barHeight;

            // Determine bar color based on state
            let color = this.colors.default;

            if (step.sorted_region && step.sorted_region.includes(index)) {
                color = this.colors.sorted;
            } else if (step.comparing && step.comparing.includes(index)) {
                color = this.colors.comparing;
            } else if (step.swapped && step.swapped.includes(index)) {
                color = this.colors.swapped;
            } else if (step.pivot === index) {
                color = this.colors.pivot;
            } else if (step.found_index === index) {
                color = this.colors.found;
            } else if (step.checking_index === index) {
                color = this.colors.comparing;
            } else if (step.mid === index) {
                color = this.colors.pivot;
            }

            // Draw bar
            this.ctx.fillStyle = color;
            this.ctx.fillRect(
                x + (barSpacing / 2),
                y,
                barWidth - barSpacing,
                barHeight
            );

            // Draw value on top of bar if space allows
            if (barWidth > 30) {
                this.ctx.fillStyle = this.colors.text;
                this.ctx.font = '12px sans-serif';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(
                    value,
                    x + (barWidth / 2),
                    y - 5
                );
            }
        });

        // Draw legend
        this.drawLegend();
    }

    drawLegend() {
        const legendItems = [
            { color: this.colors.default, label: 'Default' },
            { color: this.colors.comparing, label: 'Comparing' },
            { color: this.colors.swapped, label: 'Swapped' },
            { color: this.colors.sorted, label: 'Sorted' },
            { color: this.colors.pivot, label: 'Pivot' }
        ];

        const itemWidth = 100;
        const itemHeight = 20;
        const startX = 10;
        const startY = 10;

        legendItems.forEach((item, index) => {
            const x = startX + (index * itemWidth);

            // Draw color box
            this.ctx.fillStyle = item.color;
            this.ctx.fillRect(x, startY, 15, 15);

            // Draw label
            this.ctx.fillStyle = this.colors.text;
            this.ctx.font = '11px sans-serif';
            this.ctx.textAlign = 'left';
            this.ctx.fillText(item.label, x + 20, startY + 12);
        });
    }

    clearCanvas() {
        this.ctx.fillStyle = this.colors.background;
        this.ctx.fillRect(0, 0, this.width, this.height);
    }

    updateSpeed() {
        const value = parseInt(this.speedSlider.value);

        // Map slider value (1-10) to animation speed (1000-100 ms)
        this.animationSpeed = 1100 - (value * 100);

        // Update label
        const labels = {
            1: 'Very Slow',
            2: 'Slow',
            3: 'Slow',
            4: 'Medium-Slow',
            5: 'Medium',
            6: 'Medium-Fast',
            7: 'Fast',
            8: 'Fast',
            9: 'Very Fast',
            10: 'Very Fast'
        };
        this.speedValue.textContent = labels[value];
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorArea.style.display = 'block';
    }

    hideError() {
        this.errorArea.style.display = 'none';
    }
}

// Initialize visualizer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const visualizer = new AlgorithmVisualizer('visualization-canvas');
});
