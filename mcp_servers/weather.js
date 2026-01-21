import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import axios from "axios";

const server = new McpServer({
    name: "weather-server",
    version: "1.0.0",
});

server.tool(
    "get_weather",
    "Get current weather for a city",
    {
        city: z.string().describe("The city name (e.g., 'Sofia', 'London')"),
    },
    async ({ city }) => {
        try {
            // 1. Get coordinates using Geocoding API
            const geoUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=en&format=json`;
            const geoRes = await axios.get(geoUrl);
            
            if (!geoRes.data.results || geoRes.data.results.length === 0) {
                return { content: [{ type: "text", text: `Could not find location for: ${city}` }] };
            }

            const { latitude, longitude, name, country } = geoRes.data.results[0];

            // 2. Get real weather using coordinates
            const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true`;
            const weatherRes = await axios.get(weatherUrl);
            const weather = weatherRes.data.current_weather;

            return {
                content: [{
                    type: "text",
                    text: `Current weather in ${name}, ${country}: ${weather.temperature}°C, Wind speed: ${weather.windspeed} km/h.`
                }]
            };
        } catch (error) {
            return {
                content: [{ type: "text", text: `Error fetching weather: ${error.message}` }]
            };
        }
    }
);

const transport = new StdioServerTransport();
await server.connect(transport);