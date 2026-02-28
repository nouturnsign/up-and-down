import React, { useState } from "react";
import { Github, LineChart, Activity, Book, Menu, X, Home } from "lucide-react";

// Hardcoded mapping of plays
const PLAYS = [
  { id: "a_midsummer_nights_dream", title: "A Midsummer Night's Dream" },
  { id: "alls_well_that_ends_well", title: "All's Well That Ends Well" },
  { id: "antony_and_cleopatra", title: "Antony and Cleopatra" },
  { id: "as_you_like_it", title: "As You Like It" },
  { id: "coriolanus", title: "Coriolanus" },
  { id: "cymbeline", title: "Cymbeline" },
  { id: "hamlet", title: "Hamlet" },
  { id: "julius_caesar", title: "Julius Caesar" },
  { id: "king_henry_iv_part_1", title: "Henry IV, Part 1" },
  { id: "king_henry_iv_part_2", title: "Henry IV, Part 2" },
  { id: "king_henry_v", title: "Henry V" },
  { id: "king_henry_vi_part_1", title: "Henry VI, Part 1" },
  { id: "king_henry_vi_part_2", title: "Henry VI, Part 2" },
  { id: "king_henry_vi_part_3", title: "Henry VI, Part 3" },
  { id: "king_henry_viii", title: "Henry VIII" },
  { id: "king_john", title: "King John" },
  { id: "king_lear", title: "King Lear" },
  { id: "king_richard_ii", title: "Richard II" },
  { id: "king_richard_iii", title: "Richard III" },
  { id: "loves_labours_lost", title: "Love's Labour's Lost" },
  { id: "macbeth", title: "Macbeth" },
  { id: "measure_for_measure", title: "Measure for Measure" },
  { id: "much_ado_about_nothing", title: "Much Ado About Nothing" },
  { id: "othello", title: "Othello" },
  { id: "pericles", title: "Pericles" },
  { id: "romeo_and_juliet", title: "Romeo & Juliet" },
  { id: "the_comedy_of_errors", title: "The Comedy of Errors" },
  { id: "the_merchant_of_venice", title: "The Merchant of Venice" },
  { id: "the_merry_wives_of_windsor", title: "The Merry Wives of Windsor" },
  { id: "the_taming_of_the_shrew", title: "The Taming of the Shrew" },
  { id: "the_tempest", title: "The Tempest" },
  { id: "the_two_gentlemen_of_verona", title: "The Two Gentlemen of Verona" },
  { id: "the_two_noble_kinsmen", title: "The Two Noble Kinsmen" },
  { id: "the_winters_tale", title: "The Winter's Tale" },
  { id: "timon_of_athens", title: "Timon of Athens" },
  { id: "titus_andronicus", title: "Titus Andronicus" },
  { id: "troilus_and_cressida", title: "Troilus and Cressida" },
  { id: "twelfth_night", title: "Twelfth Night" },
];

export default function App() {
  // State to manage which HTML file is currently loaded in the iframe
  const [currentUrl, setCurrentUrl] = useState("master.html");
  const [currentTitle, setCurrentTitle] = useState(
    "Master Graph: The Complete Fortune Map",
  );

  // Mobile sidebar toggle
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Helper to update the iframe view
  const loadGraph = (url, title) => {
    setCurrentUrl(url);
    setCurrentTitle(title);
    setIsSidebarOpen(false); // Close sidebar on mobile after clicking
  };

  return (
    <div className="flex h-screen w-full bg-gray-50 overflow-hidden font-sans">
      {/* Mobile Header & Hamburger */}
      <div className="lg:hidden absolute top-0 left-0 w-full bg-slate-900 text-white p-4 flex justify-between items-center z-20 shadow-md">
        <h1 className="text-lg font-bold tracking-tight">Narrative Arcs</h1>
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="p-1"
        >
          {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <div
        className={`
        fixed inset-y-0 left-0 z-10 w-72 bg-slate-900 text-slate-300 transform transition-transform duration-300 ease-in-out flex flex-col
        ${isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0 lg:static"}
      `}
      >
        {/* Sidebar Header */}
        <div className="p-6 hidden lg:block border-b border-slate-800">
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <LineChart className="text-blue-400" />
            Arc<span className="text-blue-400">Explorer</span>
          </h1>
          <p className="text-xs text-slate-500 mt-2 uppercase tracking-wider font-semibold">
            Shakespearean Sentiment
          </p>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 overflow-y-auto py-6 px-4 pt-20 lg:pt-6 hide-scrollbar">
          {/* Master Graph Button */}
          <div className="mb-8">
            <button
              onClick={() =>
                loadGraph(
                  "master.html",
                  "Master Graph: The Complete Fortune Map",
                )
              }
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 font-medium ${
                currentUrl === "master.html"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-900/50"
                  : "hover:bg-slate-800 hover:text-white"
              }`}
            >
              <Home size={20} />
              Master Graph
            </button>
          </div>

          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 px-4">
            Individual Plays
          </h2>

          {/* List of Plays */}
          <div className="space-y-6">
            {PLAYS.map((play) => (
              <div key={play.id} className="px-2">
                <div className="flex items-center gap-2 px-2 text-slate-400 mb-2">
                  <Book size={16} />
                  <span className="font-semibold text-sm">{play.title}</span>
                </div>

                <div className="flex flex-col space-y-1 pl-6 border-l border-slate-700 ml-4">
                  <button
                    onClick={() =>
                      loadGraph(
                        `${play.id}_original.html`,
                        `${play.title} - Raw Volatility`,
                      )
                    }
                    className={`text-left text-sm px-3 py-2 rounded-md transition-colors ${
                      currentUrl === `${play.id}_original.html`
                        ? "bg-slate-800 text-blue-400 font-medium"
                        : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Activity size={14} />
                      Rolling Average
                    </div>
                  </button>

                  <button
                    onClick={() =>
                      loadGraph(
                        `${play.id}_cumulative.html`,
                        `${play.title} - Cumulative Fortune`,
                      )
                    }
                    className={`text-left text-sm px-3 py-2 rounded-md transition-colors ${
                      currentUrl === `${play.id}_cumulative.html`
                        ? "bg-slate-800 text-red-400 font-medium"
                        : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <LineChart size={14} />
                      Cumulative Arc
                    </div>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col pt-14 lg:pt-0 bg-white">
        {/* Header Bar */}
        <header className="bg-white border-b border-gray-200 px-8 py-5 flex items-center justify-between shadow-sm z-0">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 tracking-tight">
              {currentTitle}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Interactive Plotly Visualization
            </p>
          </div>
          {/* GitHub Link */}
          <a
            href="https://github.com/nouturnsign/up-and-down"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors bg-slate-100 hover:bg-slate-200 px-4 py-2 rounded-md font-medium text-sm"
          >
            <Github size={18} />
            <span className="hidden sm:inline">GitHub</span>
          </a>
        </header>

        {/* Iframe Container */}
        <main className="flex-1 relative bg-gray-50 p-4">
          <div className="absolute inset-4 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {/* The iframe loads the HTML files generated by your Python script.
              Assume this React app is hosted such that master.html and the {play}_arc.html 
              files are in the same public root directory.
            */}
            <iframe
              src={currentUrl}
              title={currentTitle}
              className="w-full h-full border-0"
              sandbox="allow-scripts allow-same-origin"
            />
          </div>
        </main>
      </div>
    </div>
  );
}
