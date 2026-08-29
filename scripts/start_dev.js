import { spawn } from 'child_process';

console.log('\x1b[36m%s\x1b[0m', '[PVC DEV] Launching Parkinson\'s Voice Companion development environment...');

// 1. Launch FastAPI Backend
const backend = spawn('python', ['-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload'], {
  stdio: 'inherit',
  shell: true,
});

// 2. Launch Vite Frontend
const frontend = spawn('npm', ['--prefix', 'frontend', 'run', 'dev'], {
  stdio: 'inherit',
  shell: true,
});

const cleanup = () => {
  console.log('\x1b[33m%s\x1b[0m', '[PVC DEV] Shutting down backend and frontend services...');
  backend.kill();
  frontend.kill();
  process.exit(0);
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
