import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
    name: "calculator-server",
    version: "1.0.0",
});

server.registerTool(
    "calculate",
    {
        title: "Addition Tool",
        description: "Perform a simple addition of two numbers",
        inputSchema: { 
            // Use z.coerce.number() to handle strings sent by the LLM
            a: z.coerce.number().describe("First number"), 
            b: z.coerce.number().describe("Second number") 
        }
    },
    async ({ a, b }) => {
        // Now 'a' and 'b' are guaranteed to be numbers
        return {
            content: [{ 
                type: "text", 
                text: String(a + b) 
            }]
        };
    }
);

const transport = new StdioServerTransport();
await server.connect(transport);