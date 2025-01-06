import React, { useState, useEffect } from "react";
import axios from "axios";

const Form_Input = () => {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/history");
        setHistory(response.data);
      } catch (err) {
        console.error("Error fetching history:", err);
      }
    };
    fetchHistory();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      setError("Question cannot be empty.");
      return;
    }
    setError("");
    setLoading(true);

    const newMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, newMessage]);

    try {
      const response = await axios.post("http://127.0.0.1:8000/ask", {
        question,
      });
      const botMessage = { role: "bot", content: response.data.answer };
      setMessages((prev) => [...prev, botMessage]);

      // Update history dynamically
      setHistory((prev) => [
        { id: Date.now(), question, answer: response.data.answer },
        ...prev,
      ]);
    } catch (err) {
      setError("Failed to get a response. Please try again.");
    } finally {
      setLoading(false);
      setQuestion("");
    }
  };

  const handleNewChat = () => {
    setSelectedChat(null);
    setMessages([]);
  };

  const handleSelectChat = (chat) => {
    setSelectedChat(chat);
    setMessages([
      { role: "user", content: chat.question },
      { role: "bot", content: chat.answer },
    ]);
  };

  return (
    <div className="flex min-h-screen">
      <div className="w-1/4 bg-gray-800 text-white overflow-y-auto">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-xl font-bold">Chat History</h2>
        </div>
        <ul>
          {history.map((chat) => (
            <li
              key={chat.id}
              className="p-4 hover:bg-gray-700 cursor-pointer"
              onClick={() => handleSelectChat(chat)}
            >
              {chat.question.slice(0, 20)}...
            </li>
          ))}
        </ul>
        <div className="p-4 mt-4">
          <button
            onClick={handleNewChat}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md w-full"
          >
            New Chat
          </button>
        </div>
      </div>
      <div className="w-3/4 bg-gray-50 flex flex-col">
        <div className="flex-grow p-6 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`p-4 rounded-md ${
                  message.role === "user" ? "bg-blue-500 text-white" : "bg-gray-200"
                }`}
              >
                {message.content}
              </div>
            ))}
          </div>
        </div>
        <form
          onSubmit={handleSubmit}
          className="p-4 border-t border-gray-300 flex items-center"
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your message..."
            rows="2"
            className="flex-grow p-2 border border-gray-300 rounded-md focus:ring focus:ring-blue-300 focus:outline-none"
          ></textarea>
          <button
            type="submit"
            className={`ml-4 px-6 py-2 rounded-md text-white font-semibold ${
              loading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-500 hover:bg-blue-600"
            }`}
            disabled={loading}
          >
            {loading ? "Loading..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Form_Input;
