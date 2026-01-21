import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
    name: "weather-server",
    version: "1.0.0",
});

// The NEW 2026 way: Use registerTool
server.registerTool(
    "get_weather",
    {
        title: "Weather Tool", // Optional display name
        description: "Get the current weather for a city",
        inputSchema: { 
            city: z.string().describe("The name of the city") 
        }
    },
    async ({ city }) => {
        return {
            content: [{ 
                type: "text", 
                text: `The weather in ${city} is 22°C and sunny.` 
            }]
        };
    }
);

const transport = new StdioServerTransport();
await server.connect(transport);