import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; 

function App() {
    const [hashtags, setHashtags] = useState('#BoycottIndia #FreeKashmir');
    const [isLoading, setIsLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');

    const [pastReports, setPastReports] = useState([]);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);

    useEffect(() => {
        const fetchPastReports = async () => {
            setIsLoadingHistory(true);
            try {
                const response = await axios.get('http://localhost:5001/api/reports');
                setPastReports(response.data.reports);
            } catch (err) {
                console.error("Failed to fetch past reports", err);
            } finally {
                setIsLoadingHistory(false);
            }
        };
        fetchPastReports();
    }, []);


    const handleAnalyzeClick = async () => {
        if (!hashtags.trim()) {
            setError('Please enter at least one hashtag.');
            return;
        }

        const hashtagsArray = hashtags.trim().split(/\s+/);
        
        setIsLoading(true);
        setResults(null);
        setError('');

        try {
            const response = await axios.post('http://localhost:5001/api/analyze', {
                hashtags: hashtagsArray,
            });
            setResults(response.data.data); 
            const reportsResponse = await axios.get('http://localhost:5001/api/reports');
            setPastReports(reportsResponse.data.reports);
        } catch (err) {
            setError('An error occurred during the analysis. Check the backend console for details.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleLoadReport = async (reportId) => {
        setIsLoading(true);
        setResults(null);
        setError('');
        try {
            const response = await axios.get(`http://localhost:5001/api/report/${reportId}`);
            setResults(response.data.data);
        } catch (err) {
            setError(`Failed to load report: ${reportId}`);
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };


    return (
        <div className="container">
            <header>
                <h1>Social Media Campaign Analyzer</h1>
                <p>Enter hashtags separated by spaces to begin analysis.</p>
            </header>

            <div className="main-content">
                <div className="analysis-section">
                    <div className="input-section">
                        <input
                            type="text"
                            value={hashtags}
                            onChange={(e) => setHashtags(e.target.value)}
                            placeholder="e.g., #hashtag1 #hashtag2"
                            disabled={isLoading}
                        />
                        <button onClick={handleAnalyzeClick} disabled={isLoading}>
                            {isLoading ? 'Analyzing...' : 'Analyze'}
                        </button>
                    </div>

                    {error && <p className="error-message">{error}</p>}

                    {isLoading && (
                        <div className="loading-container">
                            <div className="spinner"></div>
                            <p>Processing... This may take a few minutes.</p>
                            <p className="sub-text">The backend is scraping live data, so please be patient.</p>
                        </div>
                    )}
                    
                    {results && (
                        <div className="results-section">
                            <h2>Analysis Report</h2>
                            <div className="report-table">
                                <h3>Top Suspicious Users</h3>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Username</th>
                                            <th>Total Suspicion Score</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {results.userReport && results.userReport.map((row, index) => (
                                            <tr key={`user-${index}`}>
                                                <td>{row.username}</td>
                                                <td>
                                                    {row.total_suspicion_score ? parseFloat(row.total_suspicion_score).toFixed(2) : 'N/A'}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="report-table">
                                <h3>Top 20 Suspicious Tweets</h3>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Score</th>
                                            <th>Username</th>
                                            <th>Tweet Content</th>
                                            <th>Comments</th>
                                            <th>Reposts</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {results.campaignReport && results.campaignReport.slice(0, 20).map((row, index) => (
                                            <tr key={`tweet-${index}`}>
                                                <td className="score-cell">{row.suspicion_score ? parseFloat(row.suspicion_score).toFixed(2) : 'N/A'}</td>
                                                <td>{row.username || 'Unknown User'}</td>
                                                <td>{row.cleaned_content}</td>
                                                <td>{row.comments}</td>
                                                <td>{row.reposts}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
                
                <div className="history-section">
                    <h3>Past Scans</h3>
                    {isLoadingHistory ? <p>Loading history...</p> : (
                        <ul>
                            {pastReports.map(report => (
                                <li key={report.id}>
                                    <button onClick={() => handleLoadReport(report.id)} disabled={isLoading}>
                                        {report.displayName}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
}

export default App;