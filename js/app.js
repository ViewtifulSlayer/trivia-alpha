/**
 * Star Trek Trivia Generator
 * Main application logic for filtering and displaying questions
 */

class TriviaApp {
    constructor() {
        this.questions = [];
        this.filteredQuestions = [];
        this.currentIndex = 0;
        this.filters = {
            series: [],
            character: [],
            difficulty: [],
            type: [],
            source: [],
            verifiedOnly: false
        };

        this.init();
    }

    async init() {
        await this.loadQuestions();
        this.populateFilters();
        this.attachEventListeners();
        this.applyFilters();
    }

    async loadQuestions() {
        try {
            const response = await fetch('data/questions.json');
            this.questions = await response.json();
            this.updateTotalCount();
            console.log(`Loaded ${this.questions.length} questions`);
        } catch (error) {
            console.error('Error loading questions:', error);
            document.getElementById('question-text').textContent = 
                'Error loading questions. Please check that data/questions.json exists.';
        }
    }

    populateFilters() {
        // Get unique values for each filter
        const series = [...new Set(this.questions.map(q => q.series).filter(Boolean))].sort();
        const characters = [...new Set(this.questions.map(q => q.character).filter(Boolean))].sort();
        
        // Populate series filter
        const seriesSelect = document.getElementById('series-filter');
        series.forEach(s => {
            const option = document.createElement('option');
            option.value = s;
            option.textContent = s;
            seriesSelect.appendChild(option);
        });

        // Populate character filter
        const characterSelect = document.getElementById('character-filter');
        characters.forEach(c => {
            const option = document.createElement('option');
            option.value = c;
            option.textContent = c;
            characterSelect.appendChild(option);
        });
    }

    attachEventListeners() {
        // Filter change listeners
        document.getElementById('series-filter').addEventListener('change', () => this.updateFilters());
        document.getElementById('character-filter').addEventListener('change', () => this.updateFilters());
        document.getElementById('difficulty-filter').addEventListener('change', () => this.updateFilters());
        document.getElementById('type-filter').addEventListener('change', () => this.updateFilters());
        document.getElementById('source-filter').addEventListener('change', () => this.updateFilters());
        document.getElementById('verified-only').addEventListener('change', () => this.updateFilters());

        // Clear filters
        document.getElementById('clear-filters').addEventListener('click', () => this.clearFilters());

        // Navigation
        document.getElementById('prev-question').addEventListener('click', () => this.navigateQuestion(-1));
        document.getElementById('next-question').addEventListener('click', () => this.navigateQuestion(1));
        document.getElementById('random-question').addEventListener('click', () => this.randomQuestion());

        // Actions
        document.getElementById('reveal-answer').addEventListener('click', () => this.revealAnswer());
        document.getElementById('copy-question').addEventListener('click', () => this.copyQuestion());
        document.getElementById('copy-answer').addEventListener('click', () => this.copyAnswer());

        // Export
        document.getElementById('export-json').addEventListener('click', () => this.exportJSON());
        document.getElementById('export-text').addEventListener('click', () => this.exportText());
    }

    updateFilters() {
        const seriesSelect = document.getElementById('series-filter');
        const characterSelect = document.getElementById('character-filter');
        const difficultySelect = document.getElementById('difficulty-filter');
        const typeSelect = document.getElementById('type-filter');
        const sourceSelect = document.getElementById('source-filter');
        const verifiedOnly = document.getElementById('verified-only');

        this.filters.series = Array.from(seriesSelect.selectedOptions).map(o => o.value).filter(Boolean);
        this.filters.character = Array.from(characterSelect.selectedOptions).map(o => o.value).filter(Boolean);
        this.filters.difficulty = Array.from(difficultySelect.selectedOptions).map(o => o.value).filter(Boolean);
        this.filters.type = Array.from(typeSelect.selectedOptions).map(o => o.value).filter(Boolean);
        this.filters.source = Array.from(sourceSelect.selectedOptions).map(o => o.value).filter(Boolean);
        this.filters.verifiedOnly = verifiedOnly.checked;

        this.applyFilters();
    }

    applyFilters() {
        this.filteredQuestions = this.questions.filter(q => {
            // Series filter
            if (this.filters.series.length > 0 && !this.filters.series.includes(q.series)) {
                return false;
            }

            // Character filter
            if (this.filters.character.length > 0 && !this.filters.character.includes(q.character)) {
                return false;
            }

            // Difficulty filter
            if (this.filters.difficulty.length > 0 && !this.filters.difficulty.includes(q.difficulty)) {
                return false;
            }

            // Type filter
            if (this.filters.type.length > 0 && !this.filters.type.includes(q.type)) {
                return false;
            }

            // Source filter
            if (this.filters.source.length > 0 && !this.filters.source.includes(q.source)) {
                return false;
            }

            // Verified only
            if (this.filters.verifiedOnly && !q.verified) {
                return false;
            }

            return true;
        });

        this.currentIndex = 0;
        this.updateFilteredCount();
        this.displayQuestion();
    }

    clearFilters() {
        document.getElementById('series-filter').selectedIndex = 0;
        document.getElementById('character-filter').selectedIndex = 0;
        document.getElementById('difficulty-filter').selectedIndex = 0;
        document.getElementById('type-filter').selectedIndex = 0;
        document.getElementById('source-filter').selectedIndex = 0;
        document.getElementById('verified-only').checked = false;

        this.filters = {
            series: [],
            character: [],
            difficulty: [],
            type: [],
            source: [],
            verifiedOnly: false
        };

        this.applyFilters();
    }

    displayQuestion() {
        if (this.filteredQuestions.length === 0) {
            document.getElementById('question-text').textContent = 
                'No questions match the current filters. Try adjusting your filters.';
            document.getElementById('answer-section').style.display = 'none';
            document.getElementById('reveal-answer').style.display = 'none';
            document.getElementById('copy-question').style.display = 'none';
            document.getElementById('copy-answer').style.display = 'none';
            document.getElementById('question-meta').textContent = '';
            this.updateNavigation();
            return;
        }

        const question = this.filteredQuestions[this.currentIndex];
        
        // Update question text
        document.getElementById('question-text').textContent = question.question;
        
        // Update metadata
        const metaParts = [];
        if (question.series) metaParts.push(question.series);
        if (question.character) metaParts.push(question.character);
        if (question.difficulty) metaParts.push(question.difficulty);
        if (question.type) metaParts.push(question.type);
        document.getElementById('question-meta').textContent = metaParts.join(' • ');

        // Hide answer initially
        document.getElementById('answer-section').style.display = 'none';
        document.getElementById('answer-text').textContent = question.answer;
        document.getElementById('reveal-answer').style.display = 'inline-block';
        document.getElementById('copy-question').style.display = 'inline-block';
        document.getElementById('copy-answer').style.display = 'none';

        this.updateNavigation();
    }

    revealAnswer() {
        document.getElementById('answer-section').style.display = 'block';
        document.getElementById('reveal-answer').style.display = 'none';
        document.getElementById('copy-answer').style.display = 'inline-block';
    }

    navigateQuestion(direction) {
        this.currentIndex += direction;
        if (this.currentIndex < 0) this.currentIndex = this.filteredQuestions.length - 1;
        if (this.currentIndex >= this.filteredQuestions.length) this.currentIndex = 0;
        this.displayQuestion();
    }

    randomQuestion() {
        if (this.filteredQuestions.length === 0) return;
        this.currentIndex = Math.floor(Math.random() * this.filteredQuestions.length);
        this.displayQuestion();
    }

    updateNavigation() {
        const prevBtn = document.getElementById('prev-question');
        const nextBtn = document.getElementById('next-question');
        const currentIndexEl = document.getElementById('current-index');
        const totalFilteredEl = document.getElementById('total-filtered');

        currentIndexEl.textContent = this.filteredQuestions.length > 0 ? this.currentIndex + 1 : 0;
        totalFilteredEl.textContent = this.filteredQuestions.length;

        prevBtn.disabled = this.filteredQuestions.length === 0;
        nextBtn.disabled = this.filteredQuestions.length === 0;
    }

    updateFilteredCount() {
        document.getElementById('filtered-count').textContent = this.filteredQuestions.length;
    }

    updateTotalCount() {
        document.getElementById('total-count').textContent = this.questions.length;
    }

    copyQuestion() {
        if (this.filteredQuestions.length === 0) return;
        const question = this.filteredQuestions[this.currentIndex];
        navigator.clipboard.writeText(question.question).then(() => {
            alert('Question copied to clipboard!');
        });
    }

    copyAnswer() {
        if (this.filteredQuestions.length === 0) return;
        const question = this.filteredQuestions[this.currentIndex];
        navigator.clipboard.writeText(question.answer).then(() => {
            alert('Answer copied to clipboard!');
        });
    }

    exportJSON() {
        const dataStr = JSON.stringify(this.filteredQuestions, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `trivia-questions-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
    }

    exportText() {
        let text = `Star Trek Trivia Questions\n`;
        text += `Generated: ${new Date().toLocaleString()}\n`;
        text += `Total Questions: ${this.filteredQuestions.length}\n`;
        text += `\n${'='.repeat(60)}\n\n`;

        this.filteredQuestions.forEach((q, index) => {
            text += `Question ${index + 1}:\n`;
            text += `Q: ${q.question}\n`;
            text += `A: ${q.answer}\n`;
            if (q.series) text += `Series: ${q.series}\n`;
            if (q.character) text += `Character: ${q.character}\n`;
            if (q.difficulty) text += `Difficulty: ${q.difficulty}\n`;
            text += `\n${'-'.repeat(60)}\n\n`;
        });

        const dataBlob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `trivia-questions-${Date.now()}.txt`;
        link.click();
        URL.revokeObjectURL(url);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TriviaApp();
});

// Future: Rounds module (modular addition)
class RoundsManager {
    constructor(app) {
        this.app = app;
        this.rounds = [];
    }

    createRound(name, filters) {
        // Future implementation for round-based question sets
        const round = {
            name,
            filters,
            questions: this.app.filteredQuestions
        };
        this.rounds.push(round);
        return round;
    }
}

