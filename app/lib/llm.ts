import OpenAI from 'openai';

export interface QuizQuestion {
    question: string;
    answer: string;
    type: 'reading' | 'meaning' | 'grammar';
}

export const generateQuiz = async (
    content: string,
    apiKey: string,
    count: number = 10
): Promise<QuizQuestion[]> => {
    const openai = new OpenAI({
        apiKey: apiKey,
        dangerouslyAllowBrowser: true // Allowing client-side usage for this personal app
    });

    const prompt = `
    You are a Japanese language teacher. 
    Based on the following lesson notes, create ${count} review questions.
    
    The notes contain Japanese sentences, Korean translations, and grammar points.
    
    Mix the question types:
    1. Translate Korean to Japanese.
    2. Reading (Kanji to Hiragana).
    3. Meaning (Japanese to Korean).
    4. Fill in the blank (Grammar).

    Return ONLY a raw JSON array (no markdown code blocks) with this structure:
    [
      { "question": "...", "answer": "...", "type": "meaning" }
    ]

    Lesson Notes:
    ${content}
  `;

    const completion = await openai.chat.completions.create({
        messages: [{ role: 'system', content: prompt }],
        model: 'gpt-3.5-turbo',
    });

    const responseContent = completion.choices[0].message.content || '[]';

    try {
        // Clean up potential markdown code blocks if the model behaves poorly
        const cleanJson = responseContent.replace(/```json/g, '').replace(/```/g, '').trim();
        return JSON.parse(cleanJson);
    } catch (e) {
        console.error('Failed to parse LLM response', e);
        return [];
    }
};
