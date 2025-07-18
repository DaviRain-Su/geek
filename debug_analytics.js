// Debug script to test analytics functionality
// Run this in the browser console when the frontend is loaded

console.log('Starting analytics debug test...');

// Test API connectivity
async function testAPI() {
    const apiClient = window.apiClient;
    console.log('Testing API connectivity...');
    
    try {
        const response = await fetch('http://127.0.0.1:8000/health');
        console.log('Health check response:', response.ok);
        
        if (response.ok) {
            const trendsData = await apiClient.getTechnologyTrends(7);
            console.log('Trends data:', trendsData);
            
            const authorsData = await apiClient.getAuthorActivity(7);
            console.log('Authors data:', authorsData);
            
            const qualityData = await apiClient.evaluateContentQuality(10);
            console.log('Quality data:', qualityData);
            
            console.log('All API tests passed!');
        }
    } catch (error) {
        console.error('API test failed:', error);
    }
}

// Test DOM elements
function testDOM() {
    console.log('Testing DOM elements...');
    
    const analyticsSection = document.getElementById('analytics');
    console.log('Analytics section found:', !!analyticsSection);
    
    const trendsStatus = document.getElementById('trends-status');
    const trendsContent = document.getElementById('trends-content');
    console.log('Trends elements found:', { trendsStatus: !!trendsStatus, trendsContent: !!trendsContent });
    
    const analyticsModules = document.querySelectorAll('.analytics-module');
    console.log('Analytics modules found:', analyticsModules.length);
    
    return {
        analyticsSection: !!analyticsSection,
        trendsStatus: !!trendsStatus,
        trendsContent: !!trendsContent,
        moduleCount: analyticsModules.length
    };
}

// Test manual analytics loading
async function testManualAnalytics() {
    console.log('Testing manual analytics loading...');
    
    const app = window.app;
    if (!app) {
        console.error('App instance not found');
        return;
    }
    
    // Show analytics section
    app.showSection('analytics');
    
    // Wait a bit
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Test DOM after section switch
    const domTest = testDOM();
    console.log('DOM test after section switch:', domTest);
    
    // Manually trigger analytics loading
    try {
        await app.loadAnalyticsData();
        console.log('Manual analytics loading completed');
    } catch (error) {
        console.error('Manual analytics loading failed:', error);
    }
}

// Run all tests
async function runAllTests() {
    console.log('=== Analytics Debug Test Suite ===');
    
    console.log('1. Testing DOM elements...');
    const domResult = testDOM();
    console.log('DOM Test Result:', domResult);
    
    console.log('2. Testing API connectivity...');
    await testAPI();
    
    console.log('3. Testing manual analytics loading...');
    await testManualAnalytics();
    
    console.log('=== Debug Test Complete ===');
}

// Auto-run if called directly
if (typeof window !== 'undefined') {
    runAllTests();
}