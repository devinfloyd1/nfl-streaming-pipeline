# NFL Streaming Pipeline - Documentation Index

Welcome to the NFL Streaming Pipeline project! This index will help you navigate the documentation.

## 🚀 Quick Navigation

### For First-Time Users
1. **Start here:** [QUICKSTART.md](QUICKSTART.md) - Get running in 5 minutes
2. **Then read:** [README.md](README.md) - Complete project documentation
3. **Understand the code:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - File organization

### For Technical Deep Dive
1. **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md) - System design & decisions
2. **Code walkthrough:** See inline comments in Python files
3. **Configuration:** [config/settings.py](config/settings.py) - Centralized config

### For Portfolio Presentation
1. **Talking points:** [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Interview prep
2. **Demo flow:** [README.md](README.md#example-output) - What to show
3. **Key features:** [README.md](README.md#features) - What makes it special

### For Contributors
1. **Guidelines:** [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
2. **Code style:** Use `black` and `flake8`
3. **Pull requests:** Follow the PR template

## 📚 Documentation Files

| Document | Size | Purpose | Audience |
|----------|------|---------|----------|
| [README.md](README.md) | 16KB | Main documentation, setup, usage | Everyone |
| [QUICKSTART.md](QUICKSTART.md) | 5.3KB | Fast-track setup guide | New users |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 12KB | Technical deep dive | Engineers |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | 9.1KB | Portfolio talking points | Job seekers |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 11KB | File organization | Developers |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 2.4KB | Contribution guidelines | Contributors |
| [INDEX.md](INDEX.md) | 1KB | This file | Everyone |

## 💻 Code Files

| File | Lines | Purpose |
|------|-------|---------|
| [data/fetch_nfl_data.py](data/fetch_nfl_data.py) | 247 | Download NFL data from nflfastR |
| [models/train_models.py](models/train_models.py) | 386 | Feature engineering & ML training |
| [producer/kafka_producer.py](producer/kafka_producer.py) | 312 | Stream plays to Kafka topic |
| [consumer/spark_consumer.py](consumer/spark_consumer.py) | 445 | PySpark consumer with ML inference |
| [config/settings.py](config/settings.py) | ~50 | Centralized configuration |

**Total:** ~1,400 lines of production Python code

## 🛠️ Configuration Files

| File | Purpose |
|------|---------|
| [docker-compose.yml](docker-compose.yml) | Kafka infrastructure setup |
| [requirements.txt](requirements.txt) | Python dependencies |
| [.env](.env) | Environment variables |
| [Makefile](Makefile) | Convenience commands |

## 📜 Scripts

| Script | Purpose |
|--------|---------|
| [scripts/setup.sh](scripts/setup.sh) | Automated initial setup |
| [scripts/run_pipeline.sh](scripts/run_pipeline.sh) | Run complete pipeline |
| [scripts/cleanup.sh](scripts/cleanup.sh) | Clean generated files |

## 🎯 Common Tasks

### I want to...

**...get started quickly**
→ Read [QUICKSTART.md](QUICKSTART.md)

**...understand the architecture**
→ Read [ARCHITECTURE.md](ARCHITECTURE.md)

**...run the pipeline**
→ Follow [README.md](README.md#usage)

**...prepare for an interview**
→ Review [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

**...understand the code structure**
→ Check [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

**...contribute to the project**
→ Read [CONTRIBUTING.md](CONTRIBUTING.md)

**...customize for my portfolio**
→ Start with [README.md](README.md) and update author info

**...deploy to cloud**
→ See [ARCHITECTURE.md](ARCHITECTURE.md#cloud-deployment)

**...troubleshoot issues**
→ Check [QUICKSTART.md](QUICKSTART.md#common-issues) and [README.md](README.md#troubleshooting)

## 📊 Project Statistics

- **Total Documentation:** ~55KB (6 markdown files)
- **Total Code:** ~1,400 lines (4 main Python files)
- **Total Scripts:** 3 shell scripts
- **Total Config:** 4 configuration files
- **Dependencies:** 14 Python packages
- **Docker Services:** 3 (Zookeeper, Kafka, Kafka UI)

## 🎓 Learning Path

### Beginner
1. Read [README.md](README.md) introduction
2. Follow [QUICKSTART.md](QUICKSTART.md)
3. Run the pipeline locally
4. Explore [data/fetch_nfl_data.py](data/fetch_nfl_data.py) comments

### Intermediate
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Study [models/train_models.py](models/train_models.py) feature engineering
3. Understand Kafka producer/consumer pattern
4. Experiment with different games and parameters

### Advanced
1. Deep dive into PySpark streaming in [consumer/spark_consumer.py](consumer/spark_consumer.py)
2. Study ML model serving patterns
3. Plan cloud deployment
4. Implement enhancements (see [README.md](README.md#future-enhancements))

## 🔗 External Resources

### Data Source
- **nflfastR:** https://www.nflfastr.com/
- **nfl-data-py:** https://github.com/nflverse/nfl-data-py

### Technologies
- **Apache Kafka:** https://kafka.apache.org/
- **PySpark:** https://spark.apache.org/docs/latest/api/python/
- **scikit-learn:** https://scikit-learn.org/

### Learning
- **Kafka Guide:** https://www.confluent.io/resources/kafka-the-definitive-guide/
- **Spark Guide:** https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- **ML in Production:** https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/

## 📧 Support

- **Issues:** Open a GitHub issue
- **Questions:** Check [README.md](README.md#troubleshooting)
- **Contributions:** See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

**Last Updated:** January 2024  
**Version:** 1.0  
**Status:** Production Ready

**Happy Streaming! 🏈**
