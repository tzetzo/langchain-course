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
        title: "Universal Calculator",
        description: "Perform arithmetic. IMPORTANT: You must provide numbers for 'a' and 'b'.",
        inputSchema: { 
            // We use z.any() to stop Groq from blocking 'stringified' numbers
            a: z.any().describe("The first number"), 
            b: z.any().describe("The second number"),
            operation: z.enum(["add", "subtract", "multiply", "divide"])
                        .describe("The math operation")
        }
    },
    async ({ a, b, operation }) => {
        // Manually convert to numbers since Groq might send "-0.5" or -0.5
        const numA = Number(a);
        const numB = Number(b);

        if (isNaN(numA) || isNaN(numB)) {
            return {
                isError: true,
                content: [{ type: "text", text: `Invalid input: ${a} or ${b} is not a number.` }]
            };
        }

        let result;
        switch (operation) {
            case "add": result = numA + numB; break;
            case "subtract": result = numA - numB; break;
            case "multiply": result = numA * numB; break;
            case "divide": 
                if (numB === 0) return { isError: true, content: [{ type: "text", text: "Error: Division by zero" }] };
                result = numA / numB; 
                break;
        }

        return {
            content: [{ type: "text", text: String(result) }]
        };
    }
);

const transport = new StdioServerTransport();
await server.connect(transport);