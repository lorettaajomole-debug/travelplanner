const SYSTEM_PROMPT = `You are a friendly, well-traveled trip-planning expert. You help people plan trips - suggesting destinations, day-by-day itineraries, things to do, rough budgeting, and packing tips - in clear, practical language tailored to their interests, budget, dates, and travel style. Ask clarifying questions when useful, such as who is going, the budget, the season, and the preferred pace. Remind users to verify time-sensitive details themselves - visas, opening hours, prices, weather, and safety or travel advisories - since these change and you may not have current information. Be enthusiastic but realistic.`;

exports.handler = async function(event, context) {
  // CORS configuration headers
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS"
  };

  // Handle preflight OPTIONS request
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 200,
      headers: headers,
      body: ""
    };
  }

  // Only allow POST requests for chat completions
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      headers: headers,
      body: JSON.stringify({ detail: "Method Not Allowed" })
    };
  }

  // 1. Validate Environment Variables
  const endpoint = process.env.AZURE_ENDPOINT;
  const deployment = process.env.AZURE_DEPLOYMENT;
  const apiKey = process.env.AZURE_API_KEY;

  const missing = [];
  if (!endpoint || endpoint.trim() === "" || endpoint.includes("your-resource")) {
    missing.push("AZURE_ENDPOINT");
  }
  if (!deployment || deployment.trim() === "") {
    missing.push("AZURE_DEPLOYMENT");
  }
  if (!apiKey || apiKey.trim() === "" || apiKey.includes("paste-your-key")) {
    missing.push("AZURE_API_KEY");
  }

  if (missing.length > 0) {
    const errMsg = `Configuration error: Missing environment variables: ${missing.join(", ")}`;
    console.error(errMsg);
    return {
      statusCode: 500,
      headers: headers,
      body: JSON.stringify({ detail: errMsg })
    };
  }

  // 2. Parse request payload
  let messages = [];
  try {
    const data = JSON.parse(event.body);
    messages = data.messages || [];
  } catch (err) {
    return {
      statusCode: 400,
      headers: headers,
      body: JSON.stringify({ detail: "Invalid JSON in request body" })
    };
  }

  // 3. Prepend theTravel Planner system prompt
  const messagesPayload = [
    { role: "system", content: SYSTEM_PROMPT },
    ...messages.map(msg => ({ role: msg.role, content: msg.content }))
  ];

  // 4. Send request to Azure AI Foundry OpenAI completions endpoint
  // Clean endpoint base URL (remove trailing slash)
  const base = endpoint.endsWith("/") ? endpoint.slice(0, -1) : endpoint;
  const url = `${base}/chat/completions`;

  try {
    const apiResponse = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: deployment,
        messages: messagesPayload
      })
    });

    if (!apiResponse.ok) {
      const errorText = await apiResponse.text();
      console.error(`Azure OpenAI API returned error status ${apiResponse.status}: ${errorText}`);
      return {
        statusCode: 500,
        headers: headers,
        body: JSON.stringify({ detail: "Sorry, I'm having trouble answering right now..." })
      };
    }

    const result = await apiResponse.json();
    const reply = result.choices[0].message.content;

    return {
      statusCode: 200,
      headers: headers,
      body: JSON.stringify({ reply: reply })
    };

  } catch (error) {
    console.error("Error during API request execution:", error);
    return {
      statusCode: 500,
      headers: headers,
      body: JSON.stringify({ detail: "Sorry, I'm having trouble answering right now..." })
    };
  }
};
