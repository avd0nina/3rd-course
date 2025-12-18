#!/usr/bin/env python3
"""
Quick setup script for NSU Student Planner Bot
This script helps with initial configuration
"""

import os
import sys

def get_bot_token():
    print("\n" + "="*60)
    print("NSU STUDENT PLANNER BOT - SETUP")
    print("="*60)
    print("\n📖 How to get your Telegram Bot Token:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot command")
    print("3. Follow the instructions to create a bot")
    print("4. Copy the token provided by BotFather")
    print("\n")
    
    token = input("Enter your Telegram Bot Token: ").strip()
    
    if not token:
        print("❌ Token cannot be empty!")
        return None
    
    if len(token) < 10:
        print("❌ Invalid token format!")
        return None
    
    return token

def update_config(token):
    config_file = "config.py"
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Replace placeholder token
    updated_content = content.replace(
        'TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"',
        f'TELEGRAM_BOT_TOKEN = "{token}"'
    )
    
    with open(config_file, 'w') as f:
        f.write(updated_content)
    
    print("✅ Token updated in config.py")

def update_bot_file(token):
    bot_file = "bot.py"
    
    with open(bot_file, 'r') as f:
        content = f.read()
    
    # Replace placeholder token
    updated_content = content.replace(
        'TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"',
        f'TOKEN = "{token}"'
    )
    
    with open(bot_file, 'w') as f:
        f.write(updated_content)
    
    print("✅ Token updated in bot.py")

def main():
    print("\n🔧 Welcome to NSU Student Planner Bot Setup\n")
    
    # Check if already configured
    with open("bot.py", 'r') as f:
        bot_content = f.read()
    
    if 'YOUR_TELEGRAM_BOT_TOKEN' not in bot_content:
        print("⚠️  Bot already appears to be configured!")
        response = input("Do you want to reconfigure? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Skipping configuration.")
            return
    
    # Get token from user
    token = get_bot_token()
    if not token:
        print("❌ Setup failed. Please provide a valid token.")
        return
    
    # Update files
    update_config(token)
    update_bot_file(token)
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the bot: python3 bot.py")
    print("\n💡 Send /start to your bot in Telegram to begin!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
