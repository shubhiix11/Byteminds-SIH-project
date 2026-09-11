const { spawn } = require('child_process');

console.log('🚀 Starting LabelSure Backend and Frontend...\n');

// 1. Start Python Flask backend
const backend = spawn('python', ['backend/app.py'], {
  stdio: 'inherit',
  shell: true
});

// 2. Start Vite Frontend
const frontend = spawn('npm', ['--prefix', 'frontend', 'run', 'dev'], {
  stdio: 'inherit',
  shell: true
});

function handleExit() {
  console.log('\n🛑 Shutting down backend and frontend...');
  if (backend) backend.kill();
  if (frontend) frontend.kill();
  process.exit();
}

process.on('SIGINT', handleExit);
process.on('SIGTERM', handleExit);
process.on('exit', handleExit);
