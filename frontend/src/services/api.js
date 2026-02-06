import axios from 'axios';

// Automatically use the same hostname as the frontend (for local network access)
const API_HOSTNAME = window.location.hostname;
const BASE_URL = `http://${API_HOSTNAME}:8000`;

const api = axios.create({
    baseURL: `${BASE_URL}/api`,
    timeout: 30000,
});

export const authApi = axios.create({
    baseURL: `${BASE_URL}/auth`,
    timeout: 30000,
});

export const chatService = {
    // Start a new chat session
    startChat: async (userId) => {
        const formData = new FormData();
        if (userId) formData.append('user_id', userId);

        const response = await api.post('/chat/start', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    // Upload an image
    uploadImage: async (sessionId, file) => {
        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('file', file);

        const response = await api.post('/chat/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // Send a text message
    sendMessage: async (sessionId, message) => {
        const response = await api.post('/chat/message', {
            session_id: sessionId,
            message: message,
        }, {
            responseType: 'blob', // IMPORTANT: Expect binary data for images
        });

        const contentType = response.headers['content-type'];

        // Handle Image Response
        if (contentType && contentType.startsWith('image/')) {
            // Create object URL from blob
            return {
                type: 'image',
                image: response.data, // It's already a blob
                headers: response.headers,
            };
        }

        // Handle JSON Response (default)
        // We need to read the blob as text since we forced responseType: blob
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                try {
                    const data = JSON.parse(reader.result);
                    resolve(data);
                } catch (e) {
                    reject(e);
                }
            };
            reader.onerror = reject;
            reader.readAsText(response.data);
        });
    },

    // Get session info
    getSession: async (sessionId) => {
        const response = await api.get(`/chat/session/${sessionId}`);
        return response.data;
    },

    getHistory: async (userId) => {
        const response = await api.get(`/chat/history/${userId}`);
        return response.data;
    },

    deleteSession: async (sessionId) => {
        await api.delete(`/chat/session/${sessionId}`);
    },

    loadSession: async (sessionId) => {
        const response = await api.get(`/chat/session/${sessionId}`);
        return response.data;
    },

    shareSession: async (sessionId) => {
        const response = await api.post(`/chat/share/${sessionId}`);
        return response.data;
    }
};

export default api;
