#!/usr/bin/env python3
"""
AeroFace - Main Entry Point
Unified interface for face registration and check-in
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from face.register_face import register_face
from face.checkin import checkin
from face.checkout import checkout
from face.detector import detect_face


def validate_user_id(user_id):
    """
    Validate user_id format: 3-30 characters, alphanumeric, underscore, hyphen
    Returns validated user_id or None if invalid
    """
    import re
    
    user_id = user_id.strip()
    
    if not user_id:
        print("❌ Error: user_id cannot be empty")
        return None
    
    if not re.match(r"^[a-zA-Z0-9_-]{3,30}$", user_id):
        print("❌ Error: user_id must be 3-30 characters (alphanumeric, hyphen, underscore only)")
        return None
    
    return user_id


def print_menu():
    """Display main menu"""
    print("\n" + "="*50)
    print("         🔐 AEROFACE - MAIN MENU 🔐")
    print("="*50)
    print("[1] 📝 Register New Face")
    print("[2] 🟢 Check-in (Access Control)")
    print("[3] 🔵 Check-out (Log Exit)")
    print("[4] 🧪 Test Face Detection")
    print("[5] ❌ Exit")
    print("="*50)


def main():
    """Main application loop"""
    
    # Check for environment configuration
    if not os.path.exists(".env"):
        print("\n⚠️  WARNING: .env file not found!")
        print("   Please create a .env file using .env.example as template")
        print("   Copy: cp .env.example .env")
        print("   Then edit with your database credentials\n")
    
    while True:
        print_menu()
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            # Registration
            print("\n" + "-"*50)
            print("📝 FACE REGISTRATION")
            print("-"*50)
            user_id = input("Enter user ID to register: ")
            
            validated_id = validate_user_id(user_id)
            if validated_id:
                print(f"✅ Starting registration for: {validated_id}")
                print("📸 Position your face in the camera frame")
                print("🎯 Hold still for 0.5 seconds for auto-capture")
                print("⌨️  Press ESC to cancel\n")
                
                try:
                    register_face(validated_id)
                    print("✅ Registration completed successfully!")
                except KeyboardInterrupt:
                    print("\n❌ Registration cancelled by user")
                except Exception as e:
                    print(f"\n❌ Registration failed: {e}")
            
            input("\nPress ENTER to continue...")
        
        elif choice == "2":
            # Check-in
            print("\n" + "-"*50)
            print("🟢 LOUNGE CHECK-IN")
            print("-"*50)
            print("✅ Starting check-in process")
            print("📸 Look at the camera for face recognition")
            print("🎯 Hold still to get stabilization")
            print("⌨️  Press ESC to cancel\n")
            
            try:
                checkin()
                print("✅ Check-in completed!")
            except KeyboardInterrupt:
                print("\n❌ Check-in cancelled by user")
            except Exception as e:
                print(f"\n❌ Check-in failed: {e}")
            
            input("\nPress ENTER to continue...")
        
        elif choice == "3":
            # Check-out
            print("\n" + "-"*50)
            print("🔵 LOUNGE CHECK-OUT")
            print("-"*50)
            print("✅ Starting check-out process")
            print("📸 Look at the camera for face recognition")
            print("🎯 Hold still to get stabilization")
            print("⌨️  Press ESC to cancel\n")
            
            try:
                checkout()
                print("✅ Check-out completed!")
            except KeyboardInterrupt:
                print("\n❌ Check-out cancelled by user")
            except Exception as e:
                print(f"\n❌ Check-out failed: {e}")
            
            input("\nPress ENTER to continue...")
        
        elif choice == "4":
            # Face Detection Test
            print("\n" + "-"*50)
            print("🧪 FACE DETECTION TEST")
            print("-"*50)
            print("Testing face detection on live camera feed...")
            print("⌨️  Press 'q' to exit\n")
            
            try:
                detect_face()
            except KeyboardInterrupt:
                print("\n❌ Detection cancelled")
            except Exception as e:
                print(f"\n❌ Detection failed: {e}")
            
            input("\nPress ENTER to continue...")
        
        elif choice == "5":
            # Exit
            print("\n👋 Thank you for using AeroFace!")
            sys.exit(0)
        
        else:
            print("❌ Invalid choice. Please enter 1-5")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Application terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
