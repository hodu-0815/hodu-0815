export interface Lesson {
    date: string;
    month: string;
    day: string;
    content: string;
}

export interface DocData {
    [month: string]: Lesson[];
}

export const fetchDoc = async (url: string): Promise<string> => {
    // Convert standard view URL to export URL if needed
    // e.g., https://docs.google.com/document/d/DOC_ID/edit... -> https://docs.google.com/document/d/DOC_ID/export?format=txt
    let exportUrl = url;
    if (url.includes('/edit')) {
        exportUrl = url.replace(/\/edit.*/, '/export?format=txt');
    } else if (!url.includes('export?format=txt')) {
        // simple append if it matches the ID structure but missing export
        // This is a basic heuristic
        if (!url.endsWith('/')) exportUrl += '/';
        exportUrl += 'export?format=txt';
    }

    const response = await fetch(exportUrl);
    if (!response.ok) {
        throw new Error('Failed to fetch document');
    }
    return response.text();
};

export const parseDoc = (text: string): DocData => {
    const lines = text.split('\n');
    const lessons: DocData = {};

    let currentDate: string | null = null;
    let currentContent: string[] = [];

    // Regex for "@ MM-DD"
    // Allowing for some flexibility like "@ 3-19" or "@ 03-19"
    const datePattern = /^@\s*(\d{1,2}-\d{1,2})/;

    const saveLesson = (date: string, contentLines: string[]) => {
        const [month, day] = date.split('-');
        // Normalize month (e.g. "3" -> "03")
        const normalizedMonth = month.padStart(2, '0');

        if (!lessons[normalizedMonth]) {
            lessons[normalizedMonth] = [];
        }

        lessons[normalizedMonth].push({
            date,
            month: normalizedMonth,
            day,
            content: contentLines.join('\n').trim()
        });
    };

    for (let line of lines) {
        line = line.trim();
        if (!line) continue;

        const match = line.match(datePattern);
        if (match) {
            if (currentDate) {
                saveLesson(currentDate, currentContent);
            }
            currentDate = match[1];
            currentContent = [];
        } else {
            if (currentDate) {
                currentContent.push(line);
            }
        }
    }

    // Save the last one
    if (currentDate && currentContent.length > 0) {
        saveLesson(currentDate, currentContent);
    }

    return lessons;
};
