# Samvidhan V20 - Project Documentation

## 1. Project Overview
**Samvidhan** is an innovative and interactive platform designed to gamify and simplify the learning of the Indian Constitution. It bridges the gap between complex legal jargon and everyday citizens, offering an engaging way to understand constitutional rights, duties, the legislature, executive, and judiciary systems.

The platform employs a mix of AI-driven tools, interactive games, and multilingual support to make learning about the Constitution an exciting, accessible, and inclusive experience for all age groups.

---

## 2. Team Roles & Contributions

The success of this project is driven by a structured distribution of responsibilities among the team members:

- **Onkar Nanaware & Vedika Mohite**: 
  - **Roles**: End-to-End Development, Solution Architecture, Design Strategy.
  - **Contributions**: Architected the entire solution and system design. Developed the comprehensive frontend using Next.js. Engineered the core logic for all interactive games (including the Pygame-based Mario and the React-based simulations like Justice Defender and Election Strategy Builder). Integrated the frontend UI with the backend logic, Firebase for real-time leaderboards, and managed the overall aesthetic and user experience.
  
- **Tanishq Sonawane**: 
  - **Roles**: Literature Survey, AI & Prompt Engineering.
  - **Contributions**: Conducted deep literature surveys to gather structured constitutional data, curated datasets, and developed the entire Gemini AI backend pipeline. Handled AI prompt engineering to generate simplified legal stories, scenario analyses, and intelligent chatbot responses.

- **Project Guide**: Prof. Sandip Warhade

---

## 3. Technology Stack

### Frontend Architecture
- **Framework**: Next.js 14 (App Router) & React 18
- **Styling**: Tailwind CSS for responsive, modern, and aesthetic glassmorphism UI components.
- **Animations & Graphics**: Framer Motion for smooth transitions, Chart.js for data visualization.
- **Icons**: Lucide React & React Icons.
- **Multilingual Support**: Google Translate API integrated via custom React hooks to provide instant translation in 11 Indic languages (Hindi, Marathi, Kannada, Malayalam, Tamil, Telugu, Punjabi, Bengali, Gujarati, Odia, Sinhala).

### Backend Architecture
- **Framework**: Python with Flask (RESTful APIs)
- **Database**: Firebase Firestore for user progress tracking, real-time leaderboard, and user authentication management.
- **Artificial Intelligence**: `google-generativeai` (Gemini 2.5 Flash) for generating stories, conversational agents, and extracting structured JSON data from legal scenarios.
- **Computer Vision**: OpenCV (`cv2`), `cvzone`, and MediaPipe (`HandTrackingModule`) for gesture recognition in the interactive quiz game.
- **Game Engine**: Pygame for building the "Constitutional Mario" desktop game.

---

## 4. Deep Dive: Architecture & Main Logic Flow

The project is structurally divided into a Next.js Frontend and a Flask Backend, communicating asynchronously via RESTful endpoints.

### 4.1. Core Features & UI Flow

#### A. Explore Section (`/explore`)
- **UI Flow**: Displays a sidebar categorizing the Constitution into its Parts. When a Part is clicked, it dynamically loads the corresponding Articles from a local JSON dataset.
- **Logic**: Users can read the raw description of an article. If they find it complex, they can use the **Generate Story** feature.
- **AI Integration**: The frontend sends the article title to the Flask backend (`/generate-story`). The Gemini AI uses prompt engineering to create a short, simple, localized (Indian context) story to explain the legal jargon. Users can even select age groups (Kid, Teenager, Adult) for personalized explanations.

#### B. RashtraGuru Chatbot (`/chatbot`)
- **UI Flow**: A WhatsApp/Messenger-style chat interface dedicated to the Constitution.
- **Logic**: The user inputs a query, which is POSTed to the backend (`/get_response`). 
- **AI Integration**: The Gemini model is initialized with strict safety settings and a system prompt restricting it to answer *only* constitution-related queries. The conversation history is maintained on the server-side via `chat_history.json` to keep context alive across the session.

#### C. Scenario Learning (`/scenario`)
- **UI Flow**: A beautiful amber-themed layout where users type out real-life legal scenarios or doubts.
- **Logic**: Calls the `/get_scenario` Flask endpoint. 
- **AI Integration**: The `GiveGeminiOutput` function utilizes LangChain and Gemini to parse the user's unstructured scenario into structured JSON. The prompt forces the LLM to output specific arrays: `Relevant Constitutional Articles`, `Applicable Laws and Regulations`, `Simplified Explanations`, `Common Scenarios`, and `Articles`. The frontend then maps this JSON into beautifully segregated info-cards.

### 4.2. Gamification Engine (The Games)

The games section (`/games`) is the heart of the platform's engagement strategy.

#### 1. Sanvidhan Prashnamala (Hand Gesture Quiz)
- **Tech**: Python, OpenCV, MediaPipe, CVZone.
- **Logic**: Triggered from the frontend which calls the `/start-game-2` endpoint. The Flask server spawns a new multiprocessing thread (`multiprocessing.Process`) to launch the camera. MediaPipe detects hand landmarks. The distance between the index finger (landmark 8) and middle finger (landmark 12) is calculated. If the distance drops below 60 pixels while hovering over an option bounding box, it registers a "click".
- **Backend Sync**: Upon completion, the score is calculated and instantly pushed to Firebase Firestore, updating the user's global leaderboard standing.

#### 2. Constitutional Mario
- **Tech**: Pygame (`/backend/mario`).
- **Logic**: A 2D platformer. Calls `/start-game-1`. Runs locally via Python threading. Players navigate Mario through levels that impart constitutional knowledge along the way.

#### 3. Justice Defender (`/games/justice-defender`)
- **Tech**: React, Next.js.
- **Logic**: A rich, interactive TSX simulator where users act as High Court judges. They are presented with complex cases (e.g., Freedom of Speech vs. Hate Speech). They review the constitutional reference, Party A, and Party B arguments, and select judicial options. The system uses a predefined scoring logic to give them points and explains the societal impact and optimal resolution for their choices.

#### 4. Fundamental Rights Explorer (`/games/fundamental-rights-explorer`)
- **Tech**: React.
- **Logic**: 25 Real-life MCQs testing users on fundamental rights (e.g., Shopkeeper discrimination -> Article 15). 

#### 5. Election Strategy Builder (`/games/election-strategy-builder`)
- **Tech**: React.
- **Logic**: A resource management simulation. The player gets a budget (e.g., 1 Crore) and a time limit to deploy political strategies (Rallies, Social Media, Manifestos) across various districts to counter an AI opponent's influence.

#### 6. Leaderboard (`/leaderboard`)
- **Tech**: Firebase Firestore.
- **Logic**: Fetches the `users` collection from Firestore, ordering by `score` in descending order, and displays top players dynamically.

---

## 5. Presentation Strategy: How to Showcase This Project

When presenting this project to evaluators, judges, or stakeholders, follow this structured narrative to maximize impact:

### Step 1: The Problem Statement (The "Hook")
Start by mentioning that while the Indian Constitution is the backbone of our democracy, its 395 articles are buried in heavy legal jargon. *Citizens don't know their rights until they are violated.*

### Step 2: The Solution Architecture (The "Wow" Factor)
Introduce **Samvidhan V20** not just as a website, but as an ecosystem. 
- Highlight the **Tech Stack**: "We built a Next.js frontend backed by a Python Flask server, utilizing Google's cutting-edge Gemini AI and real-time Firebase tracking."
- Mention the **Multilingual capability**: Show how the site transforms into 11 regional languages instantly, breaking the English barrier.

### Step 3: Demo the AI Capabilities (Tanishq's Domain)
- Open the **Explore** section. Pick a complex article and click "Generate Story". Show how Gemini explains it to a 10-year-old child using Indian context (e.g., Ram and Shyam).
- Open the **Scenario Learner**. Type: *"My landlord kicked me out because of my religion."* Show how the AI perfectly structures the response with Article 15 references.

### Step 4: Demo the Gamification (Onkar & Vedika's Domain)
- Open **Justice Defender**. Walk the audience through the judge simulation. Explain how this builds critical thinking rather than rote memorization.
- **The Showstopper:** Run the **Sanvidhan Prashnamala (Gesture Quiz)**. Physically step back and use your fingers to answer questions on screen via webcam. Explain the OpenCV/MediaPipe architecture powering this without external hardware.
- Show the **Leaderboard** updating in real-time via Firebase after the quiz ends.

### Step 5: Team Acknowledgment
Conclude by clearly defining the roles. Appreciate Onkar and Vedika for the stunning UI/UX, seamless game engines, and full-stack integration, and Tanishq for the robust AI backend and contextual prompt engineering. 

Viewed gemini.py:1-31

Here is a breakdown of exactly how your Gemini LLM integrations are working behind the scenes for both the **Scenario** and **Story Generation** features. They actually use two slightly different approaches!



============================================================================================================================
### 1. Scenario Generation (`backend/gemini.py`)
This feature uses the **LangChain** wrapper around Gemini (`ChatGoogleGenerativeAI`) to strictly force the AI to return structured data.

*   **The Model Configuration:** It uses `gemini-2.5-flash` with the `temperature` set strictly to `0`. A temperature of 0 means the model will be highly deterministic and analytical, removing creative hallucinations, which is exactly what you want for legal advice.
*   **The Prompt Engineering:** The magic happens in the `ChatPromptTemplate`. The system prompt is highly specific. It tells the AI:
    *   Act as an advisor on the Indian Constitution.
    *   Analyze the user's scenario.
    *   **CRITICAL RULE:** It strictly commands the AI to output *only* in JSON format, requiring specific array fields: `Relevant Constitutional Articles`, `Applicable Laws and Regulations`, `Simplified Explanations of Legal Concepts`, `Common Scenarios`, and `Articles`.
*   **The Cleanup Process:** Because LLMs often wrap JSON in Markdown blocks (like ` ```json ... ``` `), your code uses a Regular Expression (`re.sub(r'^```json\s*|\s*```$', '', ai_msg.content...`) to strip away the markdown before passing it to `json.loads()`.
*   **The Flow:** The parsed JSON dictionary is passed to `server.py`, which sends it to `scenario/page.js`, where it dynamically maps those arrays into the beautiful amber-themed UI cards.

### 2. Story Generation (`backend/server.py`)
Unlike the scenario generation, the Story feature bypasses LangChain and uses the native `google.generativeai` library directly to generate creative text.

*   **The Model Configuration:** It also uses `gemini-2.5-flash`, but here you implemented strict **Safety Settings** to block Harassment, Hate Speech, Sexually Explicit, and Dangerous content. This is crucial since it's generating stories that users (including kids) will read.
*   **The Prompt Engineering:** The frontend passes the complex text of a Constitutional Article to the `/generate-story` endpoint. The server then appends this specific prompt to the text: 
    > *"Give me a very short and simple story to understand this article. Use indian context and indian names: {text}"*
*   **The Flow:** The AI processes the legal jargon and returns a creative, relatable story featuring Indian names. This raw text string (`convo.last.text`) is sent directly back to the frontend's modal window for the user to read.

### Summary of Tanishq's AI Design:
1.  **For Scenarios:** He used **LangChain + Temperature 0 + JSON Prompting** to turn unstructured user complaints into structured, factual legal databases.
2.  **For Stories:** He used **Native Gemini API + Safety Filters + Contextual Prompting** to turn complex legal jargon into creative, localized, and safe educational stories.


====================================================================================================================================================
Edited PROJECT_DOCUMENTATION.md
Viewed server.py:62-91

Here is the exact breakdown of how the **RashtraGuru Chatbot** is functioning, looking at both the frontend UI and the backend Flask integration:

### 1. The Frontend (`frontend/app/chatbot/page.js`)
*   **User Interaction:** When a user types a message and hits send, the React component instantly updates the UI to show the user's message and displays a "Thinking..." loading state.
*   **The API Call:** It triggers a `POST` request to your Flask backend (`http://localhost:5000/get_response`). It sends a JSON payload containing:
    *   `message`: The actual text the user typed.
    *   `language`: Currently hardcoded to 'English' (though you have the structure to support multilingual prompts!).
    *   `feedback`: A placeholder string.

### 2. The Backend (`backend/server.py` -> `/get_response`)
Unlike the Scenario analyzer which uses LangChain, the Chatbot uses the native `google.generativeai` SDK. Here is how Tanishq designed the AI pipeline:

*   **Initialization & Safety First:** It initializes the `gemini-2.5-flash` model and immediately applies **Safety Settings**. This ensures the bot will actively block any queries containing Harassment, Hate Speech, Sexually Explicit, or Dangerous content.
*   **The "Guardrail" Prompt Engineering:** This is the most important part. Before sending the user's message to Gemini, the code dynamically wraps it in a strict system instruction:
    > *"You are a knowledgeable assistant specializing in the Constitution of India. Answer only questions related to the Constitution in {language}. If the answer does not contain relevant constitutional keywords, inform the user accordingly: {user_message}"*
    
    *Why this is brilliant:* It prevents the AI from being misused. If a user asks "Give me a recipe for butter chicken," this prompt forces Gemini to reply "I only answer questions related to the Constitution."

### 3. Server-Side Memory Management
The chatbot has a persistence layer built into the backend to "remember" the conversation context.

*   **`chat_history.json`:** Every time a response is generated, your Python code appends a dictionary (`{"user_message": message, "response": result, "feedback": user_feedback}`) to a global `chat_history` list.
*   It then writes this entire list to a local file called `chat_history.json`.
*   This acts as a rudimentary database, ensuring that if the server restarts, the chat logs aren't entirely lost, and the API can return the full conversation history to the frontend.

### Summary
The chatbot works as a **"Guarded Conversational Agent"**. By injecting a strong personality and scope boundary into the prompt *before* it reaches Gemini, you ensure the AI remains strictly a "RashtraGuru" (a teacher of the nation) and never goes off-topic.



===========================================================================================================
Viewed ModelPretraining.js:1-10

The `markdown_converter` files (both `markdown_converter.py` in the backend and `MarkdownConverter.js` in the frontend) are essentially **Admin utility tools used for AI Data Pre-processing**.

Here is why they are in your project and their exact use case:

### 1. The Core Problem
When Tanishq (or anyone on the team) is trying to feed new legal documents, constitutional amendments, or literature into the Gemini AI (or any LLM), raw files like PDFs, Word Documents (.docx), and PowerPoints (.pptx) are incredibly messy. They contain weird formatting, invisible characters, and no clear structure. If you feed raw PDFs to an AI, the AI often gets confused and hallucinates. 

### 2. The Markdown Solution
Large Language Models (like Gemini) process **Markdown (`.md`)** files exceptionally well because Markdown uses symbols like `#` for headings to create a perfect hierarchical structure.

The `markdown_converter.py` script acts as an intelligent cleaner:
*   It uses **spaCy** (an NLP library) and **WordNet** to read uploaded PDFs/Word Docs line by line.
*   It analyzes font sizes, capitalization, and even uses linguistic logic to figure out if a line is a "Heading" or just a normal paragraph.
*   It strips out all the garbage and generates a beautifully clean `.md` file with proper `# Headings` and structured text.

### 3. How it fits into the UI (`MarkdownConverter.js`)
The `MarkdownConverter.js` provides an admin-only interface. If you have a new PDF on a recent Supreme Court ruling, an Admin can simply drag and drop that PDF into the UI. The backend runs the Python script and spits out a clean `markdown.md` file that you can download.

### Summary
These files are your **data curation pipeline**. They are used by the admins to convert messy legal literature into highly structured Markdown documents so that those documents can be safely fed into the AI models or used as clean datasets for your `data.json`!
---


======================================================================================================

Viewed PROJECT_DOCUMENTATION.md:182-197
Viewed Core.py:1-101
Viewed Player.py:1-447
Viewed Map.py:1-449

Here is the complete implementation breakdown, tech stack, data architecture, and logic for the **"Constitutional Mario"** game built within your project.

### 1. Tech Stack
Unlike the rest of your web-based games (which use React/Next.js), the Mario game runs entirely on a Python-based desktop engine.
*   **Engine:** `Pygame` (A set of Python modules designed for writing video games).
*   **Map Parsing:** `pytmx` (Used to parse Tile Map XML files into Pygame objects).
*   **Sound & Media:** Native Pygame mixer for audio (`.wav`/`.ogg`) and Pygame Image for sprite loading.

### 2. Data & Asset Architecture
The game relies heavily on external data and sprite sheets rather than hardcoded levels.
*   **Map Data (`worlds/1-1/W11.tmx`):** The entire level architecture is built using a software called "Tiled" and exported as a `.tmx` file. `Map.py` reads this file to dynamically load the ground, tubes, background scenery, and hidden blocks without having to hardcode x/y coordinates for every brick.
*   **Sprites (`images/Mario/`):** Contains the sprite sheets for Mario (moving, jumping, dying, growing).
*   **Audio:** Custom sounds loaded via `Sound.py` (e.g., `mushroom_eat`, `brick_break`, `pipe`, `fireball`).

### 3. Core Logic Breakdown
The game is split into distinct Object-Oriented classes. Here are the main pillars of the logic:

#### A. The Game Engine (`Core.py`)
This is the heartbeat of the game. It initializes the Pygame window (`WINDOW_W`, `WINDOW_H`), handles the 60 FPS clock ticking, and runs the `main_loop()`. Every frame, it executes three things:
1.  `input()`: Listens for keyboard presses (Right/Left arrows for movement, Up for jump, Shift for fireballs).
2.  `update()`: Calls the physics and collision engines.
3.  `render()`: Draws the updated positions to the screen.

#### B. Physics & Player Mechanics (`Player.py`)
This is the most complex file, handling Mario's gravity, momentum, and state.
*   **Momentum Logic:** When you hold the right arrow, Mario's `x_vel` increases by `SPEED_INCREASE_RATE` until it hits `MAX_MOVE_SPEED` (or `MAX_FASTMOVE_SPEED` if holding Shift). When you let go, he doesn't stop instantly; he slides via a `SPEED_DECREASE_RATE` friction logic.
*   **Gravity:** If `on_ground` is False, `y_vel` continuously increases by `GRAVITY` until it hits `MAX_FALL_SPEED`.
*   **State Machine (Power Levels):** 
    *   `powerLVL = 0`: Small Mario. If hit, he dies.
    *   `powerLVL = 1`: Big Mario (ate a mushroom). He can break bricks.
    *   `powerLVL = 2`: Fire Mario (ate a flower). He can shoot fireballs using `core.keyShift`.
*   **Block Interaction:** If Mario hits a block from underneath (`y_vel < 0`), it triggers `activate_block_action()`. If it's a Question block, it spawns a bonus. If it's a Brick platform and Mario is Big, it breaks it and plays the `brick_break` sound.

#### C. The World Builder (`Map.py`)
This script acts as the Director of the game.
*   **Map Parsing:** It reads the `W11.tmx` file layer by layer (Foreground vs Background).
*   **Dynamic Spawning:** Instead of spawning all enemies at once (which causes lag), it uses `try_spawn_mobs()`. For example, if Mario's `x` coordinate crosses 2080, it dynamically spawns two Goombas just off-screen.
*   **Camera Tracking:** The `oCamera` object constantly updates its offset based on Mario's `x` coordinate so that Mario stays centered and the map scrolls smoothly.
*   **Collision Detection:** Every frame, `get_blocks_for_collision()` fetches only the 14 tiles immediately surrounding Mario. This is a highly optimized way to check for collisions without having to check the entire level grid at once.

=================================================================================================
Pygame (What you are currently using)
The Language: Built entirely on Python.
How it works: It acts as a wrapper around the SDL (Simple DirectMedia Layer) library. It is designed to create Desktop Applications.
How it works in your project: When a user clicks "Play Mario" on your Next.js frontend, it sends an API call to your Flask backend. The Flask server then uses a Python script to forcibly open a separate, native desktop window to run the Mario game.
Pros: It was likely easier for Onkar and Vedika to build since the backend was already in Python, and Python makes complex logic (like custom physics and collision math) very readable.
Cons: Because it requires Python to run, users cannot play the Mario game simply by visiting your website on their phone or a random computer; they would need your Python backend running locally.

### Summary
The Mario implementation is a beautifully structured, highly optimized Pygame loop. By utilizing external `.tmx` files and strict Object-Oriented physics classes, it recreates the exact momentum-based feel of the original 1985 Super Mario Bros.
*Generated by AI Assistant for Samvidhan V20 Team.*
