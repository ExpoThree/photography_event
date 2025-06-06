## Overview
- A Discord bot to manage image submissions in a specific channel.
- Uses SQLite to track and limit user submissions.
- Designed for fair and organized entry collection.

## Key Features
- Only allows image attachments in the submissions channel.
- Each user can submit only one image; additional submissions are blocked.
- Moderators can delete all submissions with a slash command.

## Usage
- Set your Discord token in a `.env` file.
- Configure channel, role, and guild IDs in the code.
- Bot uses `keep_alive` for persistent hosting.

## Benefits
- Prevents spam and duplicate entries.
- Simplifies moderation for contests or events.
- Keeps submission channels clean and organized.

readme by perplexity
