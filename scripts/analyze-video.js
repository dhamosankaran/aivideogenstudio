// analyze-video.js
import fs from "fs";
import path from "path";
import { GoogleGenerativeAI } from "@google/generative-ai";

const apiKey = process.env.GEMINI_API_KEY;
if (!apiKey) {
    throw new Error("Set GEMINI_API_KEY env var first");
}

const genAI = new GoogleGenerativeAI(apiKey);

// Helper to convert a local file into the inlineData format Gemini expects
function fileToGenerativePart(filePath, mimeType = "video/mp4") {
    const data = fs.readFileSync(filePath);
    return {
        inlineData: {
            data: data.toString("base64"),
            mimeType,
        },
    };
}

async function analyzeVideo(videoPath) {
    const model = genAI.getGenerativeModel({
        model: "gemini-2.5-flash", // or newer model id as docs update
    });

    const videoPart = fileToGenerativePart(videoPath, "video/mp4");

    const prompt = `
You are a visual QA assistant.

Analyze this video and return ONLY valid JSON.

Schema:
{
  "status": "pass" | "fail",
  "issues": [
    {
      "time": "HH:MM:SS or second index",
      "description": "short description of the visual issue",
      "severity": "low" | "medium" | "high"
    }
  ],
  "summary": "short human-readable summary"
}

Focus ONLY on what is visible on screen (UI glitches, layout problems, missing elements, flicker, wrong colors, etc.).
`;

    const result = await model.generateContent({
        contents: [
            {
                role: "user",
                parts: [
                    { text: prompt },
                    videoPart,
                ],
            },
        ],
    });

    const text = result.response.text();
    console.log("Raw model output:");
    console.log(text);

    // Optional: try to parse JSON if the model obeyed the schema
    try {
        const jsonStart = text.indexOf("{");
        const jsonEnd = text.lastIndexOf("}");
        const jsonStr = text.slice(jsonStart, jsonEnd + 1);
        const parsed = JSON.parse(jsonStr);
        console.log("\nParsed JSON:\n", JSON.stringify(parsed, null, 2));
        return parsed;
    } catch (e) {
        console.error("Failed to parse JSON, handle manually:", e);
        return { raw: text };
    }
}

// Usage: node analyze-video.js ./output/run-123.mp4
const videoArg = process.argv[2];
if (!videoArg) {
    console.error("Usage: node analyze-video.js <path-to-video.mp4>");
    process.exit(1);
}

const absPath = path.resolve(videoArg);
analyzeVideo(absPath).catch(console.error);
