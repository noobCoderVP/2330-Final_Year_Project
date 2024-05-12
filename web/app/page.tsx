"use client"
import Image from "next/image";
import { useEffect, useState } from "react";

export default function Home() {
    const [messages, setMessages] = useState<string[]>([]);

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8765");

        socket.onopen = () => {
            console.log("WebSocket connected!");
        };

        socket.onmessage = (event) => {
            const message = event.data;
            console.log(message);
            setMessages((prevMessages) => [...prevMessages, message]);
        };

        
        return () => {
          socket.close();
        };
      }, []);

    const onButtonClick = () => {
      const socket = new WebSocket("ws://localhost:8765");
      console.log(messages);
      socket.onopen = () => {
        socket.send("Hello world 2");
        console.log("Message sent");
      };
    }
    return (
        <main>
            <div>
              <button className="px-4 py-2 bg-black text-white" onClick={onButtonClick}>
                Send message
              </button>
                {messages.map((value, index) => {
                    return <li key={index}>{value}</li>;
                })}
            </div>
        </main>
    );
}
