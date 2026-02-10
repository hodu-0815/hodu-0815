'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchDoc, parseDoc, DocData, Lesson } from './lib/parser';
import { Settings, BookOpen, Calendar, ChevronRight, Loader2 } from 'lucide-react';

export default function Home() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [docData, setDocData] = useState<DocData | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const init = async () => {
            const docUrl = localStorage.getItem('japanese_doc_url');
            const apiKey = localStorage.getItem('japanese_api_key');

            if (!docUrl || !apiKey) {
                router.push('/settings');
                return;
            }

            try {
                const text = await fetchDoc(docUrl);
                const data = parseDoc(text);
                setDocData(data);
            } catch (err) {
                setError('Failed to load document. Please check the URL.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        init();
    }, [router]);

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-50 text-gray-500">
                <Loader2 className="animate-spin mr-2" /> Loading your lessons...
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col h-screen items-center justify-center bg-gray-50 p-4">
                <div className="text-red-500 mb-4">{error}</div>
                <Link href="/settings" className="text-blue-500 underline">
                    Go to Settings
                </Link>
            </div>
        );
    }

    return (
        <main className="min-h-screen bg-gray-50 p-4 md:p-8">
            <header className="max-w-3xl mx-auto flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Japanese Lessons</h1>
                    <p className="text-gray-500 text-sm">Review your daily progress</p>
                </div>
                <Link href="/settings" className="p-2 bg-white rounded-full shadow-sm hover:shadow-md transition">
                    <Settings className="w-5 h-5 text-gray-600" />
                </Link>
            </header>

            <div className="max-w-3xl mx-auto space-y-8">
                {docData && Object.entries(docData).map(([month, lessons]) => (
                    <section key={month} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <h2 className="text-lg font-semibold text-gray-800 flex items-center">
                                <Calendar className="w-5 h-5 mr-2 text-indigo-500" />
                                {month} Month
                            </h2>
                            <Link
                                href={`/quiz?month=${month}`}
                                className="text-xs font-medium bg-indigo-50 text-indigo-600 px-3 py-1.5 rounded-full hover:bg-indigo-100 transition"
                            >
                                Review Month
                            </Link>
                        </div>
                        <div className="divide-y divide-gray-50">
                            {lessons.map((lesson) => (
                                <div key={lesson.date} className="p-4 hover:bg-gray-50 transition flex justify-between items-center group">
                                    <div className="flex items-center">
                                        <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-pink-500 font-bold text-sm mr-4">
                                            {lesson.day}
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-900">
                                                Lesson {lesson.date}
                                            </p>
                                            <p className="text-xs text-gray-400 line-clamp-1 mt-0.5">
                                                {lesson.content.slice(0, 50)}...
                                            </p>
                                        </div>
                                    </div>
                                    <Link
                                        href={`/quiz?date=${lesson.date}`}
                                        className="opacity-0 group-hover:opacity-100 transition flex items-center text-sm font-medium text-gray-600 hover:text-pink-500"
                                    >
                                        Start Quiz <ChevronRight className="w-4 h-4 ml-1" />
                                    </Link>
                                </div>
                            ))}
                        </div>
                    </section>
                ))}
            </div>
        </main>
    );
}
