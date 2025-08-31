const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const cors = require('cors');
const csv = require('csv-parser');
const crypto = require('crypto');

const app = express();
app.use(cors());
app.use(express.json());

const SCRIPTS_DIR = path.join(__dirname, '..', '..');
const REPORTS_DIR = path.join(__dirname, 'reports');
const SCRAPER_SCRIPT = path.join(SCRIPTS_DIR, 'x_Scarper.py');
const PROCESS_ANALYZE_SCRIPT = path.join(SCRIPTS_DIR, 'process_and_analyze.py');
const SCRAPER_STATIC_OUTPUT = path.join(SCRIPTS_DIR, 'scraped_data.json');

fs.mkdir(REPORTS_DIR, { recursive: true }).catch(console.error);

const runScript = (scriptPath, args = []) => {
    return new Promise((resolve, reject) => {
        console.log(`Executing: python "${scriptPath}" ${args.join(' ')}`);
        
        const process = spawn('python', [scriptPath, ...args], { cwd: SCRIPTS_DIR });

        let stdout = '';
        let stderr = '';

        process.stdout.on('data', (data) => {
            console.log(`[${path.basename(scriptPath)}]: ${data.toString()}`);
            stdout += data.toString();
        });
        process.stderr.on('data', (data) => {
            console.error(`[${path.basename(scriptPath)} ERROR]: ${data.toString()}`);
            stderr += data.toString();
        });
        
        process.on('close', (code) => {
            if (code !== 0) {
                const error = new Error(`Script ${path.basename(scriptPath)} exited with code ${code}. Stderr: ${stderr}`);
                return reject(error);
            }
            console.log(`Finished executing ${path.basename(scriptPath)}.`);
            resolve(stdout);
        });
    });
};

const cleanupTempFiles = async (files) => {
    console.log(`--- Cleaning up temporary files ---`);
    for (const file of files) {
        try {
            await fs.unlink(file);
            console.log(`Deleted temp file: ${file}`);
        } catch (err) {
            if (err.code !== 'ENOENT') { 
                console.error(`Failed to delete temporary file: ${file}`, err);
            }
        }
    }
};

app.get('/api/reports', async (req, res) => {
    try {
        const files = await fs.readdir(REPORTS_DIR);
        const reportIds = files
            .filter(file => file.startsWith('campaign_analysis_report_'))
            .map(file => file.replace('campaign_analysis_report_', '').replace('.csv', ''))
            .sort((a, b) => b.localeCompare(a));

        const reports = reportIds.map(id => {
            const [hashtag, date] = id.split('_');
            return {
                id: id,
                displayName: `${hashtag} (${date})`
            };
        });

        res.json({ success: true, reports });
    } catch (err) {
        console.error("Error listing reports:", err);
        res.status(500).json({ success: false, message: "Could not retrieve report list." });
    }
});

app.get('/api/report/:reportId', async (req, res) => {
    const { reportId } = req.params;
    const campaignFile = path.join(REPORTS_DIR, `campaign_analysis_report_${reportId}.csv`);
    const userFile = path.join(REPORTS_DIR, `suspicious_users_report_${reportId}.csv`);
    
    try {
        const campaignResults = [];
        const userResults = [];
        
        const readCampaignReport = new Promise((resolve, reject) => {
             fsSync.createReadStream(campaignFile)
                .pipe(csv())
                .on('data', (data) => campaignResults.push(data))
                .on('end', resolve)
                .on('error', reject);
        });

        const readUserReport = new Promise((resolve, reject) => {
            fsSync.createReadStream(userFile)
                .pipe(csv())
                .on('data', (data) => userResults.push(data))
                .on('end', resolve)
                .on('error', reject);
        });

        await Promise.all([readCampaignReport, readUserReport]);
        
        res.json({
            success: true,
            data: {
                campaignReport: campaignResults,
                userReport: userResults
            }
        });
    } catch (err) {
        console.error(`Error reading report ${reportId}:`, err);
        res.status(500).json({ success: false, message: `Could not load report: ${reportId}` });
    }
});

app.post('/api/analyze', async (req, res) => {
    const { hashtags } = req.body;
    if (!hashtags || !Array.isArray(hashtags) || hashtags.length === 0) {
        return res.status(400).json({ success: false, message: 'Hashtags are required as an array.' });
    }

    const runId = crypto.randomBytes(16).toString('hex');
    console.log(`--- Starting Pipeline for run_id: ${runId} ---`);
    
    const tempScraperFile = path.join(SCRIPTS_DIR, `scraped_data_${runId}.json`);
    const tempPreprocessedFile = path.join(SCRIPTS_DIR, `preprocessed_twitter_data_${runId}.csv`);
    const filesToCleanup = [tempScraperFile, tempPreprocessedFile, SCRAPER_STATIC_OUTPUT];

    const today = new Date().toISOString().split('T')[0];
    const reportBaseName = `${hashtags[0].replace('#','')}_${today}`;
    const finalReportFile = path.join(REPORTS_DIR, `campaign_analysis_report_${reportBaseName}.csv`);
    const finalUserReportFile = path.join(REPORTS_DIR, `suspicious_users_report_${reportBaseName}.csv`);

    try {
        await runScript(SCRAPER_SCRIPT, hashtags);
        
        await fs.rename(SCRAPER_STATIC_OUTPUT, tempScraperFile);
        
        await runScript(PROCESS_ANALYZE_SCRIPT, [
            runId,
            finalReportFile,
            finalUserReportFile
        ]);

        console.log('--- Pipeline Complete ---');

        const campaignResults = [];
        const userResults = [];
        
        const readCampaignReport = new Promise((resolve, reject) => {
             fsSync.createReadStream(finalReportFile)
                .pipe(csv())
                .on('data', (data) => campaignResults.push(data))
                .on('end', resolve)
                .on('error', reject);
        });

        const readUserReport = new Promise((resolve, reject) => {
            fsSync.createReadStream(finalUserReportFile)
                .pipe(csv())
                .on('data', (data) => userResults.push(data))
                .on('end', resolve)
                .on('error', reject);
        });

        await Promise.all([readCampaignReport, readUserReport]);

        res.json({
            success: true,
            data: {
                campaignReport: campaignResults,
                userReport: userResults
            }
        });
        
    } catch (err) {
        console.error(`Error during pipeline for run_id: ${runId}`, err);
        res.status(500).json({ success: false, message: "An error occurred during analysis." });
    } finally {
        await cleanupTempFiles(filesToCleanup);
    }
});

const PORT = 5001;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));