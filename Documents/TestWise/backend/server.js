require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { CohereClient } = require('cohere-ai');
const { generateSitemap } = require('./sitemap');

const app = express();
const PORT = process.env.PORT || 5000;

// Security headers with Helmet
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: [
        "'self'",
        "'unsafe-inline'", // Helaas nodig voor React
        "'unsafe-eval'",   // Helaas nodig voor React development
        "https://apis.google.com"
      ],
      styleSrc: [
        "'self'",
        "'unsafe-inline'", // CSS inline styles
        "https://fonts.googleapis.com"
      ],
      imgSrc: [
        "'self'",
        "data:",
        "https:",
        "blob:",
        "https://firebasestorage.googleapis.com",
        "https://*.firebasestorage.app"
      ],
      connectSrc: [
        "'self'",
        "https://api.cohere.ai",
        "https://testwise-62ebd.firebaseio.com",
        "https://firestore.googleapis.com",
        "https://identitytoolkit.googleapis.com",
        "https://securetoken.googleapis.com",
        "https://*.googleapis.com",
        "wss://*.firebaseio.com"
      ],
      fontSrc: [
        "'self'",
        "data:",
        "https://fonts.gstatic.com"
      ],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'", "blob:"],
      frameSrc: ["'none'"],
      baseUri: ["'self'"],
      formAction: ["'self'"],
      frameAncestors: ["'none'"],
      upgradeInsecureRequests: process.env.NODE_ENV === 'production' ? [] : null
    },
  },
  crossOriginEmbedderPolicy: false,
  crossOriginResourcePolicy: { policy: "cross-origin" },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// Gzip/Brotli compression
app.use(compression());

// CORS Middleware - Restrict to specific origins
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = process.env.NODE_ENV === 'production'
      ? [
          'https://testwise.nl',
          'https://www.testwise.nl',
          'https://testwise-62ebd.web.app',
          'https://testwise-62ebd.firebaseapp.com'
        ]
      : [
          'http://localhost:3000',
          'http://localhost:5000',
          'http://127.0.0.1:3000'
        ];

    // Allow requests with no origin (mobile apps, Postman, etc.)
    if (!origin || allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 86400 // 24 hours
};

app.use(cors(corsOptions));

// Body parser
app.use(express.json());

// Initialize Cohere client
const cohere = new CohereClient({
  token: process.env.COHERE_API_KEY,
});

// ========================================
// RATE LIMITING
// ========================================

// General API rate limiter (voor alle /api routes)
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minuten
  max: 100, // Max 100 requests per 15 min
  message: 'Te veel verzoeken van dit IP. Probeer over 15 minuten opnieuw.',
  standardHeaders: true,
  legacyHeaders: false,
  // Trust proxy if behind reverse proxy (Vercel, etc.)
  trustProxy: process.env.NODE_ENV === 'production'
});

// Strict rate limiter voor AI grading endpoint
const aiGradingLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minuut
  max: 10, // Max 10 requests per minuut (vanwege API costs)
  message: 'Te veel AI nakijk verzoeken. Probeer over 1 minuut opnieuw.',
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: false,
  trustProxy: process.env.NODE_ENV === 'production'
});

// Apply general rate limiter to all API routes
app.use('/api/', apiLimiter);

// AI Grading Endpoint (met extra strict rate limiting)
app.post('/api/grade-open-question', aiGradingLimiter, async (req, res) => {
  try {
    const { studentAnswer, answerModel, questionText, teacherId, maxPoints } = req.body;

    // Validation
    if (!studentAnswer || !questionText) {
      return res.status(400).json({
        error: 'studentAnswer en questionText zijn verplicht'
      });
    }

    if (!teacherId) {
      return res.status(401).json({
        error: 'Niet geautoriseerd'
      });
    }

    // Validate maxPoints
    const questionMaxPoints = parseInt(maxPoints) || 10;
    if (questionMaxPoints < 1 || questionMaxPoints > 100) {
      return res.status(400).json({
        error: 'maxPoints moet tussen 1 en 100 zijn'
      });
    }

    // Check if answer model is provided
    if (!answerModel || answerModel.trim() === '') {
      return res.status(400).json({
        error: 'Geen antwoordmodel beschikbaar. AI kan niet nakijken zonder antwoordmodel.'
      });
    }

    // Build prompt for Cohere - gebruik directe punten
    const prompt = `Je bent een ervaren docent die een open vraag nakijkt.

VRAAG:
${questionText}

ANTWOORDMODEL (wat de docent als juist heeft aangegeven):
${answerModel}

ANTWOORD VAN LEERLING:
${studentAnswer}

BELANGRIJK: Deze vraag is maximaal ${questionMaxPoints} punten waard.

Beoordeel dit antwoord en geef:
1. PUNTEN: Een cijfer tussen 0 en ${questionMaxPoints} punten
   - 0 punten = volledig fout of geen relevant antwoord
   - ${questionMaxPoints} punten = perfect antwoord met alle kernpunten
   - Gebruik tussenliggende waarden voor gedeeltelijk correcte antwoorden
   - Je mag decimalen gebruiken (bijv. 0.5, 1.5, 2.5)
2. FEEDBACK: 2-3 zinnen feedback voor de leerling
   - Wat goed was
   - Wat ontbrak of fout was
   - Concreet en constructief
3. ONDERBOUWING: Korte uitleg waarom dit aantal punten

Wees streng maar eerlijk. Het antwoord hoeft niet exact te zijn, maar moet de kernpunten bevatten.

Antwoord ALLEEN in dit JSON format (grade is een getal tussen 0 en ${questionMaxPoints}):
{
  "grade": 1.5,
  "feedback": "Je feedback hier...",
  "reasoning": "Je onderbouwing hier..."
}`;

    // Call Cohere API
    const response = await cohere.chat({
      model: 'command-r-plus-08-2024',
      message: prompt,
      temperature: 0.3,
      maxTokens: 1024,
    });

    // Parse response
    const responseText = response.text;

    // Extract JSON from response
    let result;
    try {
      // Try to find JSON in the response
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        result = JSON.parse(jsonMatch[0]);
      } else {
        result = JSON.parse(responseText);
      }
    } catch (parseError) {
      console.error('Failed to parse Claude response:', responseText);
      return res.status(500).json({
        error: 'Kon AI response niet verwerken',
        rawResponse: responseText
      });
    }

    // Validate result - verwacht grade
    if (typeof result.grade !== 'number' || result.grade < 0 || result.grade > questionMaxPoints) {
      console.error(`Invalid grade from AI: ${result.grade} (max: ${questionMaxPoints})`);
      return res.status(500).json({
        error: `Ongeldig cijfer van AI ontvangen (moet tussen 0 en ${questionMaxPoints} zijn)`
      });
    }

    console.log(`✅ AI Grading: ${result.grade}/${questionMaxPoints} punten`);

    // Return result
    res.json({
      grade: result.grade,
      feedback: result.feedback || '',
      reasoning: result.reasoning || '',
      aiGenerated: true,
      model: 'command-r-plus-08-2024',
      gradedAt: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error grading question:', error);

    if (error.statusCode === 401 || error.message?.includes('api key')) {
      return res.status(500).json({
        error: 'Ongeldige API key. Controleer COHERE_API_KEY in .env'
      });
    }

    res.status(500).json({
      error: 'Fout bij AI nakijken',
      details: error.message
    });
  }
});

// Sitemap route
app.get('/sitemap.xml', async (req, res) => {
  try {
    const sitemap = await generateSitemap();
    res.header('Content-Type', 'application/xml');
    res.header('Cache-Control', 'public, max-age=86400'); // Cache for 24 hours
    res.send(sitemap);
  } catch (error) {
    console.error('Error generating sitemap:', error);
    res.status(500).send('Error generating sitemap');
  }
});

// Robots.txt route (optional - can also serve from public folder)
app.get('/robots.txt', (req, res) => {
  res.type('text/plain');
  res.header('Cache-Control', 'public, max-age=86400'); // Cache for 24 hours
  res.send(`# robots.txt voor TestWise
User-agent: *
Allow: /
Sitemap: https://testwise.nl/sitemap.xml`);
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString()
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Backend server running on port ${PORT}`);
  console.log(`Cohere API Key configured: ${process.env.COHERE_API_KEY ? 'Yes' : 'No'}`);
});
