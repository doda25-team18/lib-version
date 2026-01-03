# TestWise Backend - AI Grading Service

Dit is de backend service voor AI-nakijken met Claude API.

## Setup

### 1. Installeer Dependencies

```bash
cd backend
npm install
```

### 2. Configureer API Key

Bewerk het `.env` bestand en voeg je Anthropic API key toe:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
PORT=5000
```

Om een API key te krijgen:
1. Ga naar https://console.anthropic.com/
2. Maak een account aan of log in
3. Ga naar "API Keys"
4. Maak een nieuwe API key aan
5. Kopieer de key en plak deze in `.env`

### 3. Start de Backend Server

```bash
npm start
```

Of voor development met auto-reload:

```bash
npm run dev
```

De server draait nu op `http://localhost:5000`

## API Endpoints

### POST /api/grade-open-question

Nakijken van een open vraag met AI.

**Request Body:**
```json
{
  "studentAnswer": "Het antwoord van de leerling...",
  "answerModel": "Het correcte antwoord volgens de docent...",
  "questionText": "De vraag tekst...",
  "teacherId": "uid_van_docent"
}
```

**Response:**
```json
{
  "grade": 7.5,
  "feedback": "Feedback voor de leerling...",
  "reasoning": "Onderbouwing van het cijfer...",
  "aiGenerated": true,
  "model": "claude-sonnet-4-20250514",
  "gradedAt": "2024-01-01T12:00:00.000Z"
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## Rate Limiting

- Maximaal 10 verzoeken per minuut per IP-adres
- Dit is om API kosten te beperken

## Security

- API key wordt NOOIT naar de frontend gestuurd
- Alleen ingelogde docenten kunnen de API gebruiken
- CORS is ingeschakeld voor `http://localhost:3000`

## Model

Gebruikt: **claude-sonnet-4-20250514**

Dit is het nieuwste en meest capabele Claude model, ideaal voor nakijkwerk.

## Kosten

Geschatte kosten per vraag: ~$0.01 - $0.03 afhankelijk van lengte antwoorden.

Let op: houd je API gebruik in de gaten via https://console.anthropic.com/

## Troubleshooting

### "Ongeldige API key" error

- Controleer of je API key correct is in `.env`
- Zorg dat er geen spaties voor of na de key staan
- Controleer of je account credits heeft

### CORS errors

- Zorg dat de backend draait op port 5000
- Controleer dat de frontend draait op port 3000

### Rate limiting

- Wacht 1 minuut voordat je het opnieuw probeert
- Of gebruik de batch grading met ingebouwde delays
