# 📸 Discord Submission Bot

A Discord bot to manage image submissions for events or contests.

## ⚙️ Features
- Only allows **image** submissions in a specified channel
- Each user can post **only one** image
- Automatically creates a **thread** for each submission
- Deletes thread if original message is deleted
- Moderators can clear all submissions via a slash command
- Stores data in **SQLite**

## 🚀 Usage
1. Set your bot token in a `.env` file:
DISCORD_TOKEN=your-token
2. Configure `SUBMISSIONS_CHANNEL`, `MODERATOR_ROLE`, and `GUILD_ID` in the script
3. Run with `python bot.py`

## ✅ Benefits
- Prevents spam & duplicate submissions
- Clean and organized image channel
- Makes contests easy to manage

> Designed for simplicity, fairness, and automation.

readme by OpenAI
