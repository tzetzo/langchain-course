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
        description: "Perform basic arithmetic: add, subtract, multiply, or divide",
        inputSchema: { 
            a: z.coerce.number().describe("First number"), 
            b: z.coerce.number().describe("Second number"),
            operation: z.enum(["add", "subtract", "multiply", "divide"])
                        .describe("The math operation to perform")
        }
    },
    async ({ a, b, operation }) => {
        let result;
        switch (operation) {
            case "add": result = a + b; break;
            case "subtract": result = a - b; break;
            case "multiply": result = a * b; break;
            case "divide": 
                if (b === 0) return { isError: true, content: [{ type: "text", text: "Error: Division by zero" }] };
                result = a / b; 
                break;
        }
        return {
            content: [{ type: "text", text: String(result) }]
        };
    }
);

const transport = new StdioServerTransport();
await server.connect(transport);