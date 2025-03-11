# TrustMirage

![2025-03-11 16_05_59-KALI  Running  - Oracle VirtualBox _ 1](https://github.com/user-attachments/assets/bf05abc6-6d31-4c40-8955-64acb3f5b664)


A Python-based ethical hacking toolkit for phishing simulations, credential harvesting, and security awareness training.

**Created by**: koreyhacks_

## 🚨 DISCLAIMER 🚨

This tool is for **ETHICAL HACKING** and **SECURITY TESTING** purposes only. Always obtain proper authorization before conducting security tests. The author is not responsible for any misuse of this tool.

## Features

- Clone websites from URLs
- Clone websites from screenshots 
- Harvest credentials for security analysis
- Track user interactions in real-time
- Generate security reports
- Easy-to-use command-line interface

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/koreyhacks/trustmirage.git
   cd trustmirage
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python trustmirage.py
```

The tool will display an interactive menu with the following options:

1. **Clone website from URL** - Clone an existing website by providing its URL
2. **Clone website from screenshot** - Take a screenshot and generate a phishing site based on it
3. **View harvested credentials** - View credentials captured during your phishing simulations
4. **Settings** - Configure tool settings
5. **Help** - View documentation and usage instructions
6. **Exit** - Exit the application

### Cloning from URL

This method fetches the HTML from a target website, modifies it to redirect form submissions to your local server, and starts a web server to host the cloned site.

### Cloning from Screenshot

This feature allows you to take a screenshot of a website and generate a phishing page based on the visual elements captured. This is useful for quickly replicating sites without needing to fetch and parse HTML.

### Viewing Harvested Credentials

The tool logs all captured credentials to the `harvested` directory. You can view these files directly or use the built-in viewer.

## Security Recommendations

When conducting phishing simulations or security awareness training:

1. Always obtain proper written authorization
2. Document all testing activities
3. Handle captured credentials with care
4. Inform users after the test is complete
5. Use the results to improve security awareness

## Technical Details

TrustMirage works by:

1. Fetching target websites or using screenshots
2. Modifying HTML forms to redirect submissions
3. Setting up a local web server to capture data
4. Storing captured information securely
5. Providing analysis and reporting tools

## Requirements

See `requirements.txt` for a full list of dependencies:

```
pillow
beautifulsoup4
requests
```

## Results

Below are examples of TrustMirage in action, demonstrating its capabilities:

### Cloning a Website
![2025-03-11 16_09_01-KALI  Running  - Oracle VirtualBox _ 1](https://github.com/user-attachments/assets/00f979ac-5e8d-43d1-8a8b-e89c31718617)

The screenshot above shows:
1. TrustMirage's main menu with options for cloning, viewing credentials, and configuration
2. The user selecting option 1 to clone a website from URL
3. Entering the target URL (https://www.koreyhacks.io/) and port (8080)
4. The tool successfully fetching the website content
5. Warning that no forms were found in the target HTML
6. The server successfully starting on localhost:8080
7. Information about the phishing site being active with URLs to access it

### Cloned Website Result
![2025-03-11 16_11_58-KALI  Running  - Oracle VirtualBox _ 1](https://github.com/user-attachments/assets/923513a7-7cdd-408d-ba8f-e168e29ee2c2)

The screenshot above shows:
1. The cloned website running on localhost:8080
2. A perfect replica of the target website (koreyhacks.io)
3. The Matrix-style background with green code rain effect
4. Navigation menu with Home, Blog, Projects, and About sections
5. "Ethical Hacking Journey" as the main headline
6. Journal entries about SMB Relay Attacks and PsExec Exploitation
7. The browser's address bar showing localhost:8080, confirming this is the cloned site

This demonstration shows how TrustMirage can effectively clone a website for security testing purposes. The cloned site appears identical to the original, making it an effective tool for phishing simulations and security awareness training.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Contact

For questions, feedback, or issues, please contact:
- GitHub: @koreyhacks
