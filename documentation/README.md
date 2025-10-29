# 📚 Schulmanager Online Integration - Documentation Index

Complete documentation for the Schulmanager Online Home Assistant Integration.

---

## 🚀 Quick Start

| Document | Description |
|----------|-------------|
| [Configuration Guide](Configuration_Guide.md) | How to set up and configure the integration |
| [Troubleshooting Guide](Troubleshooting_Guide.md) | Common issues and solutions |
| [Automation Examples](Automation_Examples.md) | Ready-to-use automation examples |

---

## 🔑 API Documentation

### Core APIs

| Document | Description |
|----------|-------------|
| [Authentication Guide](Authentication_Guide.md) | How authentication works (PBKDF2-SHA512) |
| [API Analysis](API_Analysis.md) | Overview of available API endpoints |
| [API Implementation](API_Implementation.md) | Implementation details and patterns |
| [API Token Scope Review](API_Token_Scope_Review.md) | Understanding JWT token scoping |

### **🆕 NEW: Institution API** ⭐

| Document | Description |
|----------|-------------|
| [**Institution API Documentation**](Institution_API_Documentation.md) | **Complete guide to fetching school names and details** |
| [Institution API Summary](INSTITUTION_API_SUMMARY.md) | Quick reference for institution endpoints |

> **Discovery:** October 29, 2025 - Found 5 working endpoints that provide full institution details (name, address, contact info) for single-school accounts!

### Feature-Specific APIs

| Document | Description |
|----------|-------------|
| [Schedules API Documentation](Schedules_API_Documentation.md) | Schedule/timetable endpoints and data structures |
| [Homework API Documentation](Homework_API_Documentation.md) | Homework retrieval and management |
| [Exams API Documentation](Exams_API_Documentation.md) | Exams and assessments data |
| [Letters API Documentation](Letters_API_Documentation.md) | School letters and communications |

---

## 🏫 Multi-School Support

| Document | Description |
|----------|-------------|
| [Multi-School Complete Guide](Multi_School_Complete_Guide.md) | Comprehensive guide to multi-school account handling |
| [Automatic Multi-School Implementation](Automatic_Multi_School_Implementation.md) | Technical implementation details |
| [Institution Info Implementation](Institution_Info_Implementation.md) | How institution names are stored and displayed |
| [Multi-School Debug Script Guide](Multi_School_Debug_Script_Guide.md) | Testing multi-school configurations |
| [BUGFIX: Multi-School v1.0.7](BUGFIX_Multi_School_v1.0.7.md) | Critical bug fix for multi-school salt handling |

---

## 📊 Sensors & Features

| Document | Description |
|----------|-------------|
| [Sensors Documentation](Sensors_Documentation.md) | All available sensors and their attributes |
| [Sensor Refactoring 2025](Sensor_Refactoring_2025.md) | Latest sensor architecture improvements |
| [Free Hours Implementation](free-hours-implementation.md) | Free period detection and display |
| [Custom Card Documentation](Custom_Card_Documentation.md) | UI card features and configuration |

---

## 🔧 Development & Troubleshooting

| Document | Description |
|----------|-------------|
| [Development Setup](Development_Setup.md) | Setting up a development environment |
| [Integration Architecture](Integration_Architecture.md) | Technical architecture overview |
| [Docker Guide](Docker_Guide.md) | Running Home Assistant in Docker for testing |
| [Debug Information Collection](Debug_Information_Collection.md) | How to collect debug logs for issues |
| [Schedule API Troubleshooting](Schedule_API_Troubleshooting.md) | Specific troubleshooting for schedule issues |

---

## 🎯 Key Features by Topic

### For End Users

**Getting Started:**
1. [Configuration Guide](Configuration_Guide.md) - Setup instructions
2. [Troubleshooting Guide](Troubleshooting_Guide.md) - Solve common issues
3. [Automation Examples](Automation_Examples.md) - Copy-paste automations

**Multi-School Accounts:**
1. [Multi-School Complete Guide](Multi_School_Complete_Guide.md) - Everything about multi-school
2. [Institution Info Implementation](Institution_Info_Implementation.md) - How school names are handled

**Understanding Your Data:**
1. [Sensors Documentation](Sensors_Documentation.md) - What each sensor shows
2. [Schedules API Documentation](Schedules_API_Documentation.md) - Schedule data structure

### For Developers

**API Integration:**
1. [Authentication Guide](Authentication_Guide.md) - Implement authentication
2. [**Institution API Documentation**](Institution_API_Documentation.md) - **Get school details**
3. [API Implementation](API_Implementation.md) - Implementation patterns

**Multi-School Development:**
1. [Automatic Multi-School Implementation](Automatic_Multi_School_Implementation.md) - Architecture
2. [API Token Scope Review](API_Token_Scope_Review.md) - Token behavior
3. [Multi-School Debug Script Guide](Multi_School_Debug_Script_Guide.md) - Testing tools

**Contributing:**
1. [Development Setup](Development_Setup.md) - Dev environment
2. [Integration Architecture](Integration_Architecture.md) - System design
3. [Debug Information Collection](Debug_Information_Collection.md) - Debug patterns

---

## 📝 Recent Updates

### October 29, 2025
- ✨ **NEW:** [Institution API Documentation](Institution_API_Documentation.md) - Discovered API endpoints to fetch full school details
- 🔍 Found 5 working endpoints: `main/get-institution`, `settings/get-institution`, `admin/get-institution`, `profile/get-institution`, `user/get-institution`
- ✅ Solves the single-school account name issue - no more "School 13309"!

### Previous Updates
- See individual document headers for version history and change logs

---

## 🤝 Contributing to Documentation

Found an error or want to improve the docs?

1. All documentation is in Markdown format
2. Use clear headings and examples
3. Include code samples where relevant
4. Update this index when adding new docs

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/rwunsch/schulmanager-online-hass/issues)
- **Discussions:** [GitHub Discussions](https://github.com/rwunsch/schulmanager-online-hass/discussions)
- **Home Assistant Community:** [Community Forum Thread](https://community.home-assistant.io/) *(if available)*

---

*Last Updated: October 29, 2025*

