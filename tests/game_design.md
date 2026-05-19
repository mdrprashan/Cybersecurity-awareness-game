# CyberQuest Game Module Design

## 1. Game Design

CyberQuest is an educational cybersecurity awareness game designed to improve students’ understanding of common cyber threats through interactive learning. The system applies gamification principles to encourage participation, engagement, and knowledge retention. Research in cybersecurity education shows that game-based learning improves motivation and helps learners better understand security concepts in practical scenarios.

The game focuses on three important cybersecurity areas:
- Phishing Awareness
- Password Security
- Safe Browsing

These categories were selected because phishing attacks, weak passwords, and unsafe browsing are among the most common causes of cybersecurity incidents identified by organizations such as OWASP and NIST.

The quiz-based structure allows students to learn through realistic scenarios and immediate feedback. Students gain points and badges as rewards for completing challenges, which increases motivation and encourages continued learning.

---

## 2. Challenge Module Implementation

The challenge module was developed using Flask and Bootstrap 5. Quiz questions are stored in the database using the Challenge model. Each question contains:
- category
- difficulty
- points
- four multiple-choice answers
- correct answer

The system includes 15 questions divided equally across the three cybersecurity categories. Difficulty levels are:
- Easy
- Medium
- Hard

Each difficulty level awards different points:
- Easy = 10
- Medium = 20
- Hard = 30

Students answer questions through a web interface. The system automatically validates answers, calculates scores, and stores results in the database. Flask routes handle quiz flow, feedback, and progress tracking.

---

## 3. Badge and Reward System

The badge system was implemented to motivate users and improve engagement. Students earn achievement badges when they complete specific milestones.

Examples include:
- Phishing Expert
- Password Pro
- Safe Surfer
- CyberQuest Champion
- Perfect Score

The badge system encourages students to complete all categories and achieve higher scores. Gamification techniques such as rewards and progress tracking are widely supported in cybersecurity education research because they increase user participation and learning outcomes.

The system prevents duplicate badge awards by checking existing user achievements before assigning new badges.

---

## 4. Progress Tracking

The progress tracking module allows students to monitor their learning journey. The dashboard displays:
- Total score
- Completion percentage
- Recent activity
- Earned badges

Progress bars are used to visually represent completion status. Students can identify strengths and weaknesses across cybersecurity topics.

The system stores user scores and challenge completion history in the database. This information can help instructors monitor student engagement and learning performance.

---

## 5. User Testing

User testing is important to evaluate usability, educational value, and engagement. Testing would involve students interacting with the CyberQuest platform and completing quiz challenges.

Feedback collected would include:
- Ease of navigation
- Question difficulty
- User interface design
- Motivation provided by badges and rewards
- Educational effectiveness

The collected feedback would be used to improve the interface, adjust question difficulty, and enhance overall gameplay experience. Additional improvements may include adding timers, leaderboards, and more advanced cybersecurity scenarios.