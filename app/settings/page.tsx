'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Save } from 'lucide-react';

export default function Settings() {
    const router = useRouter();
    const [docUrl, setDocUrl] = useState('');
    const [apiKey, setApiKey] = useState('');

    useEffect(() => {
        setDocUrl(localStorage.getItem('japanese_doc_url') || '');
        setApiKey(localStorage.getItem('japanese_api_key') || '');
    }, []);

    const handleSave = () => {
        localStorage.setItem('japanese_doc_url', docUrl);
        localStorage.setItem('japanese_api_key', apiKey);
        router.push('/');
    };

    return (
        <main className="min-h-screen bg-gray-50 p-4 flex items-center justify-center">
            <div className="bg-white max-w-md w-full rounded-2xl shadow-xl p-8 border border-gray-100">
                <div className="flex items-center mb-8">
                    <Link href="/" className="mr-4 text-gray-400 hover:text-gray-600">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <h1 className="text-2xl font-bold text-gray-900">App Settings</h1>
                </div>

                <div className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Google Doc URL (Public/Link-accessible)
                        </label>
                        <input
                            type="text"
                            value={docUrl}
                            onChange={(e) => setDocUrl(e.target.value)}
                            placeholder="https://docs.google.com/document/..."
                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pink-500 focus:border-transparent outline-none transition"
                        />
                        <p className="text-xs text-gray-400 mt-2">
                            Make sure the doc is visible to "Anyone with the link".
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            OpenAI API Key
                        </label>
                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="sk-..."
                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pink-500 focus:border-transparent outline-none transition"
                        />
                        <p className="text-xs text-gray-400 mt-2">
                            Stored locally in your browser. Used to generate quizzes.
                        </p>
                    </div>

                    <button
                        onClick={handleSave}
                        className="w-full bg-pink-500 hover:bg-pink-600 text-white font-bold py-3 rounded-xl transition flex items-center justify-center shadow-lg shadow-pink-200"
                    >
                        <Save className="w-4 h-4 mr-2" />
                        Save & Continue
                    </button>
                </div>
            </div>
        </main>
    );
}
