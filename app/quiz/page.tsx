'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { fetchDoc, parseDoc, Lesson, saveDocData } from '../lib/parser';
import { generateQuiz, QuizQuestion } from '../lib/llm';
import { ArrowLeft, RefreshCw, XCircle, CheckCircle, Eye, EyeOff } from 'lucide-react';

// Wrapper component to handle search params
function QuizContent() {
    const searchParams = useSearchParams();
    const dateParam = searchParams.get('date');
    const monthParam = searchParams.get('month');

    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [questions, setQuestions] = useState<QuizQuestion[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showAnswer, setShowAnswer] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadQuiz = async () => {
            const docUrl = localStorage.getItem('japanese_doc_url');
            const apiKey = localStorage.getItem('japanese_api_key');

            if (!docUrl || !apiKey) {
                setError('Configuration missing. Please go to settings.');
                setLoading(false);
                return;
            }

            try {
                setGenerating(true);
                const text = await fetchDoc(docUrl);
                const data = parseDoc(text);

                let contentToQuiz = '';

                if (dateParam) {
                    // Find specific lesson
                    let foundLesson: Lesson | undefined;
                    Object.values(data).forEach(lessons => {
                        const hit = lessons.find(l => l.date === dateParam);
                        if (hit) foundLesson = hit;
                    });
                    if (foundLesson) {
                        contentToQuiz = foundLesson.content;
                    }
                } else if (monthParam) {
                    // Combine all lessons in month
                    const lessons = data[monthParam];
                    if (lessons) {
                        contentToQuiz = lessons.map(l => l.content).join('\n\n');
                    }
                }

                if (!contentToQuiz) {
                    setError('No content found for the selected date/month.');
                    setLoading(false);
                    setGenerating(false);
                    return;
                }

                const quizData = await generateQuiz(contentToQuiz, apiKey);
                setQuestions(quizData);
            } catch (err) {
                console.error(err);
                setError('Failed to generate quiz. Please check your API key and connection.');
            } finally {
                setLoading(false);
                setGenerating(false);
            }
        };

        loadQuiz();
    }, [dateParam, monthParam]);

    if (loading || generating) {
        return (
            <div className="flex flex-col h-screen items-center justify-center bg-gray-50 text-gray-600">
                <div className="w-16 h-16 border-4 border-pink-200 border-t-pink-500 rounded-full animate-spin mb-4"></div>
                <p className="animate-pulse font-medium">
                    {generating ? "AI is crafting your quiz..." : "Loading content..."}
                </p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col h-screen items-center justify-center bg-gray-50 p-6 text-center">
                <XCircle className="w-12 h-12 text-red-400 mb-4" />
                <h2 className="text-xl font-bold text-gray-800 mb-2">Oops!</h2>
                <p className="text-gray-500 mb-6">{error}</p>
                <Link href="/" className="text-pink-500 font-medium hover:underline">
                    Return Home
                </Link>
            </div>
        );
    }

    if (questions.length === 0) {
        return (
            <div className="flex flex-col h-screen items-center justify-center bg-gray-50 p-6 text-center">
                <p className="text-gray-500 mb-6 font-medium">No questions generated.</p>
                <p className="text-gray-400 text-sm mb-6">The lesson content might be too short or the AI returned an empty response.</p>
                <Link href="/" className="text-pink-500 font-medium hover:underline">
                    Return Home
                </Link>
            </div>
        )
    }

    const currentQuestion = questions[currentIndex];
    const isLast = currentIndex === questions.length - 1;

    const nextQuestion = () => {
        if (!isLast) {
            setCurrentIndex(prev => prev + 1);
            setShowAnswer(false);
        }
    };

    return (
        <main className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-gray-100 p-4 flex items-center justify-between shadow-sm sticky top-0 z-20">
                <Link href="/" className="p-2 rounded-full hover:bg-gray-100 transition">
                    <ArrowLeft className="w-5 h-5 text-gray-600" />
                </Link>
                <div className="font-mono text-sm font-semibold text-gray-400">
                    Question {currentIndex + 1} of {questions.length}
                </div>
                <button onClick={() => window.location.reload()} className="p-2 rounded-full hover:bg-gray-100 transition" title="New Quiz">
                    <RefreshCw className="w-5 h-5 text-gray-600" />
                </button>
            </header>

            {/* Card */}
            <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-2xl mx-auto w-full">
                <div className="w-full bg-white rounded-3xl shadow-xl overflow-hidden min-h-[400px] flex flex-col relative border border-gray-100/50">
                    {/* Question Type Badge */}
                    <div className="bg-gradient-to-r from-pink-500 to-rose-500 text-white text-xs font-bold px-4 py-2 absolute top-0 left-0 rounded-br-2xl uppercase tracking-wider shadow-sm z-10">
                        {currentQuestion.type}
                    </div>

                    {/* Content */}
                    <div className="flex-1 flex flex-col items-center justify-center p-8 text-center z-10">
                        <h2 className="text-2xl md:text-3xl font-bold text-gray-800 leading-relaxed mb-8">
                            {currentQuestion.question}
                        </h2>

                        {showAnswer && (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300 w-full">
                                <div className="text-3xl md:text-4xl font-bold text-indigo-600 mb-2 break-words">
                                    {currentQuestion.answer}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="p-6 bg-gray-50 border-t border-gray-100 flex-none grid grid-cols-1 gap-4">
                        {!showAnswer ? (
                            <button
                                onClick={() => setShowAnswer(true)}
                                className="w-full py-4 rounded-xl bg-white border-2 border-indigo-100 text-indigo-600 font-bold text-lg hover:bg-indigo-50 hover:border-indigo-200 transition shadow-sm flex items-center justify-center"
                            >
                                <Eye className="w-5 h-5 mr-2" />
                                Reveal Answer
                            </button>
                        ) : (
                            <button
                                onClick={nextQuestion}
                                disabled={isLast && showAnswer} // Actually logic is: if isLast, should show finish
                                className={`w-full py-4 rounded-xl font-bold text-lg shadow-lg flex items-center justify-center transition focus:scale-[0.98] active:scale-[0.98]
                            ${isLast
                                        ? 'bg-green-500 text-white cursor-default shadow-green-200'
                                        : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200'
                                    }`}
                            >
                                {isLast ? (
                                    <Link href="/" className="w-full h-full flex items-center justify-center">
                                        <CheckCircle className="w-5 h-5 mr-2" />
                                        Finish Review
                                    </Link>
                                ) : (
                                    "Next Question"
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}

export default function Quiz() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center text-gray-500">Loading quiz interface...</div>}>
            <QuizContent />
        </Suspense>
    );
}
