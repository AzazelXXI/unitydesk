// Simple CDN server for file uploads and static serving
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const UPLOAD_DIR = path.join(__dirname, 'uploads');
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, UPLOAD_DIR);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + '-' + file.originalname);
  }
});
const upload = multer({ storage });

const app = express();
app.use(cors());
app.use('/cdn', express.static(UPLOAD_DIR));

// In-memory metadata store for demo (replace with DB in production)
let attachmentIdCounter = 1;
const attachmentMeta = {};

// File upload endpoint
app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ success: false, message: 'No file uploaded' });
  }
  const fileUrl = `/cdn/${req.file.filename}`;
  // Simulate DB insert and return an ID
  const id = attachmentIdCounter++;
  attachmentMeta[id] = {
    id,
    url: fileUrl,
    filename: req.file.originalname,
    mimetype: req.file.mimetype,
    size: req.file.size
  };
  res.json({ success: true, ...attachmentMeta[id] });
});

const PORT = process.env.CDN_PORT || 4001;
app.listen(PORT, () => {
  console.log(`CDN server running at http://localhost:${PORT}/cdn/`);
});
