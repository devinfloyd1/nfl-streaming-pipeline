# Contributing Guidelines

Thank you for your interest in contributing to the NFL Streaming Pipeline project!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/nfl-streaming-pipeline.git
   cd nfl-streaming-pipeline
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to all functions/classes
- Keep functions focused and small
- Add comments for complex logic

### Formatting

Use `black` for code formatting:
```bash
black data/ models/ producer/ consumer/
```

Use `flake8` for linting:
```bash
flake8 data/ models/ producer/ consumer/ --max-line-length=100
```

## Testing

(Tests to be implemented - future enhancement)

```bash
pytest tests/ -v
```

## Commit Messages

Use clear, descriptive commit messages:

```
Good:
- "Add XGBoost model for win probability"
- "Fix Kafka connection timeout issue"
- "Update README with deployment instructions"

Bad:
- "fix bug"
- "update"
- "changes"
```

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request with:
   - Clear title and description
   - Link to any related issues
   - Screenshots/examples if applicable

## Areas for Contribution

### High Priority
- [ ] Add unit tests for feature engineering
- [ ] Add integration tests for pipeline
- [ ] Implement XGBoost models
- [ ] Add Prometheus metrics
- [ ] Create Grafana dashboards

### Medium Priority
- [ ] ESPN API integration for live data
- [ ] React dashboard for visualizations
- [ ] AWS deployment scripts
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Data quality tests

### Documentation
- [ ] Video tutorial
- [ ] Blog post walkthrough
- [ ] Jupyter notebook examples
- [ ] API documentation

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Questions about the code
- Documentation improvements

## Code of Conduct

Be respectful and constructive in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
