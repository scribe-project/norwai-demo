import React, { useState, useRef, useEffect } from 'react';
import { post } from "./api"

const HOST = "localhost"
// change to your local ip to access from other devices
// const HOST = "12.34.56.789"
const PORT = "8080"
const URL = `http://${HOST}:${PORT}`

const programMap = {
  "NorgeRundtDef": "Norge Rundt - De Frivillige",
  "Debatten12okt": "Debatten - 12. oktober",
  "Debatten19okt": "Debatten - 19. oktober",
  "6899tilegdør": "Kjartan Lauritzen - 6899 til eg dør"
}
const TVProgramSelector = ({ tvPrograms, onChange }) => {
  return (
    <select onChange={onChange} defaultValue="">
      <option value="" disabled>Programmer</option>
      {tvPrograms.map((tvProgram, index) => (
        <option key={index} value={tvProgram}>{programMap[tvProgram.replace(".jsonl", "")]}</option>
      ))}
    </select>
  );
}


function App() {
  const videoRef = useRef(null);
  const [query, setQuery] = useState('');
  const [currentTimestamp, setCurrentTimestamp] = useState(0);
  const [lastUpdatedTimestamp, setLastUpdatedTimestamp] = useState(0);
  const [history, setHistory] = useState([]);
  const [validTranscriptions, setValidTranscriptions] = useState([]);
  const [selectedTranscription, setSelectedTranscription] = useState(null);
  const [currentSubtitle, setCurrentSubtitle] = useState("");
  const [k, setK] = useState(1);
  const [ready, setReady] = useState(false);

  // fetch valid transcriptions from /transcriptions get endpoint
  useEffect(() => {
    const fetchTranscriptions = async () => {
      const res = await fetch(`${URL}/transcriptions`);
      const data = await res.json();
      console.log("fetched transcriptions", data)
      setValidTranscriptions(data);
    }
    fetchTranscriptions();
  }, [])

  useEffect(() => {
    const updateSubtitle = async () => {
      const video = videoRef.current;
      const currentTime = video.currentTime;
      if (Math.abs(currentTime - currentTimestamp) > 1) {
        const res = await post(
          `${URL}/subtitle`,
          JSON.stringify({ timestamp: currentTime }))
        console.log(res)
        setCurrentTimestamp(currentTime);
        setCurrentSubtitle(res)
        // ensure that each subtitle is shown for at least 2 seconds
        // if (Math.abs(currentTime - lastUpdatedTimestamp) > 2) {
        //   setLastUpdatedTimestamp(currentTime);
        // }
      }
    };
    const video = videoRef.current;
    if (ready) {
      video.addEventListener("timeupdate", updateSubtitle);
      return () => {
        video.removeEventListener("timeupdate", updateSubtitle);
      };
    }
  }, [currentTimestamp, setCurrentTimestamp, videoRef, ready]);

  const handleTvShowSelect = async (e) => {
    setReady(false)
    const selectedTvProgram = e.target.value;
    setSelectedTranscription(selectedTvProgram);
    // send a post request to /update with the selected program
    const res = await post(`${URL}/update`, JSON.stringify({ path: selectedTvProgram }))
    if (res.status === "ok") {
      setReady(true);
    }
  }

  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  }

  const searchVideos = async (e) => {
    e.preventDefault();
    const res = await post(
      `${URL}/search`,
      JSON.stringify({ text: query, k }))

    // const timeStr = res.map(timestamp => {
    //   return `${parseFloat(timestamp["start"]).toFixed(2)}-->${parseFloat(timestamp["end"]).toFixed(2)}`
    // });

    const timestamp = res[0]["time"]
    // videoRef.current.currentTime = timestamp;
    // videoRef.current.play();
    const historyString = `${query} (${timestamp}sec.)`
    // add history if the element does not exist
    if (!history.includes(historyString)) {
      setHistory([historyString, ...history])
    }

    for (const tt of res) {
      videoRef.current.currentTime = tt["time"];
      videoRef.current.play();
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  };

  const handleHistoryClick = (historyString) => {
    // from     const historyString = `${query} (${timestamp})`
    // extract the timestamp as a float:
    const timestamp = parseFloat(historyString.split("(")[1].split("sec.)")[0])
    if (timestamp) {
      videoRef.current.currentTime = timestamp;
      videoRef.current.play();
    }
  }

  const videoPath = selectedTranscription ? require(`./assets/${selectedTranscription}.mp4`) : null;

  return (
    <div className="App">
      <header className="App-header">
        <div id="header-left">
          <h1>Automatiske undertekster og semantisk søk i TV-programmer</h1>
          <h3>SCRIBE demo @NorwAI</h3>
        </div>
        <div id="header-right">
          <img width={128} src={require("./assets/qr_scribe.png")} alt="QR code" />
          <a href="https://scribe-project.github.io/">scribe-project.github.io</a>
        </div>
      </header>
      <div className="content" style={{
        "display": "flex",
        "flexDirection": "row",
        "justifyContent": "space-between",
      }}>
        <div className="video-container">
          {(!ready && !selectedTranscription) && (
            <h2 style={{ color: "lightgray" }}>Velg et program fra listen --></h2>
          )}
          {(!ready && selectedTranscription) && (
            <h2 style={{ color: "lightgray" }}>Laster inn programmet...</h2>
          )}
          {ready && (
            <div id="video-and-sub">
              <video ref={videoRef} src={videoPath} type="video/mp4" controls autoPlay />
              <div id="subtitle">
                {currentSubtitle && <p>{currentSubtitle.text}</p>}
              </div>
            </div>
          )}
        </div>
        <div className="search-history-container">
          <div className="file-selector">
            <h4>Velg et program:</h4>
            <TVProgramSelector tvPrograms={validTranscriptions} onChange={handleTvShowSelect} />
          </div>
          {ready && (
            <>
              <h4>Semanitsk søk:</h4>
              <form onSubmit={searchVideos}>
                <input type="text" value={query} onChange={handleQueryChange} required placeholder="Tekst for semantisk søk, f.eks 'holdninger til vaksine'" />
                {query && (
                  <>
                    <h5 style={{ color: "white" }}>Søk</h5>
                    <button type="submit" disabled={!query}>Transcription search</button>
                    {/* show k value */}
                    <p style={{ color: "white" }}>Antall treff: {k}</p>
                    {/* slider to select k */}
                    <input type="range" min="1" max="10" value={k} onChange={(e) => setK(parseInt(e.target.value))} />
                  </>
                )}
              </form>
              <div className="search-history">
                {history.map((item, index) => (
                  <div key={index} className="search-history-item" onClick={() => handleHistoryClick(item)}>
                    <p>{item}</p>
                    <hr />
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
