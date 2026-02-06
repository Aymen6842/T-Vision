import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        host: true, // Listen on all network interfaces
        proxy: {
            '/api': {
                // target 'localhost' is perfect because it refers to the machine
                // where the dev server and backend are BOTH running.
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    }
})
