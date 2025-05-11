/**
 * Test script for Scribley API endpoints
 * Run with: node test-api.js
 */

// Import fetch for Node.js environment
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

const API_BASE_URL = 'http://127.0.0.1:8080/api';
// Get token from environment variable
const MEDIUM_TOKEN = process.env.MEDIUM_API_TOKEN || '';

// Check if token is available
if (!MEDIUM_TOKEN) {
  console.error('\n❌ ERROR: No Medium API token found!');
  console.error('Please set your Medium API token as an environment variable:');
  console.error('export MEDIUM_API_TOKEN=your_token_here\n');
  process.exit(1);
}

async function testEndpoint(url, description) {
  console.log(`\nTesting ${description}...`);
  try {
    // Add Medium token as header for authentication
    const headers = {
      'Authorization': `Bearer ${MEDIUM_TOKEN}`,
      'Accept': 'application/json'
    };
    
    console.log(`Making request to: ${url}`);
    const response = await fetch(url, { headers });
    const status = response.status;
    
    console.log(`Status: ${status} (${response.statusText})`);
    
    // Only log safe headers, not all headers
    const safeHeaders = {};
    if (response.headers.has('content-type')) safeHeaders['content-type'] = response.headers.get('content-type');
    if (response.headers.has('x-total-count')) safeHeaders['x-total-count'] = response.headers.get('x-total-count');
    console.log('Response headers:', safeHeaders);
    
    try {
      // Try to read the response as text first
      const text = await response.text();
      
      // Only show length, not full response content
      console.log(`Response length: ${text.length} bytes`);
      
      // Then try to parse as JSON if possible
      let data = null;
      try {
        data = JSON.parse(text);
        // Sanitize output - show structure but not full content
        const sanitizedData = sanitizeResponseData(data);
        console.log('Parsed JSON response structure:', JSON.stringify(sanitizedData, null, 2));
      } catch (jsonError) {
        console.log('Not a valid JSON response');
      }
      
      if (!response.ok) {
        console.log('❌ Failed');
        return false;
      }
      
      console.log('✅ Success');
      return true;
    } catch (e) {
      console.log('Error processing response:', e.message);
      console.log('❌ Failed');
      return false;
    }
  } catch (error) {
    console.log(`Error: ${error.message}`);
    console.log('❌ Failed');
    return false;
  }
}

/**
 * Sanitizes the response data to avoid exposing sensitive information
 * Replaces actual values with type information or truncated content
 */
function sanitizeResponseData(data) {
  if (!data) return null;
  
  // Handle arrays
  if (Array.isArray(data)) {
    if (data.length === 0) return [];
    // For arrays, just show type and count
    return `Array with ${data.length} items of type ${typeof data[0]}`;
  }
  
  // Handle objects
  if (typeof data === 'object') {
    const result = {};
    // For each key, show type but not full content
    for (const key in data) {
      if (typeof data[key] === 'object' && data[key] !== null) {
        result[key] = Array.isArray(data[key]) ? 
          `Array with ${data[key].length} items` : 
          `Object with keys: ${Object.keys(data[key]).join(', ')}`;
      } else {
        // For strings, show truncated content
        if (typeof data[key] === 'string' && data[key].length > 20) {
          result[key] = `${data[key].substring(0, 20)}... (${data[key].length} chars)`;
        } else {
          result[key] = `${typeof data[key]}: ${data[key]}`;
        }
      }
    }
    return result;
  }
  
  // Handle primitives
  return data;
}

async function checkBackendConnection() {
  console.log('\n--- Testing API Server Connection ---');
  try {
    const headers = {
      'Authorization': `Bearer ${MEDIUM_TOKEN}`
    };
    
    const response = await fetch('http://127.0.0.1:8080/', { headers });
    const status = response.status;
    console.log(`API Server Status: ${status} (${response.statusText})`);
    
    if (response.ok) {
      const text = await response.text();
      try {
        const data = JSON.parse(text);
        // Only show type, not content
        console.log(`API Server Response: ${typeof data} with keys: ${Object.keys(data).join(', ')}`);
      } catch (e) {
        console.log(`API Server Response: Text (${text.length} bytes)`);
      }
      console.log('✅ Backend server is running!');
    } else {
      console.log('❌ Backend server returned an error status');
    }
  } catch (error) {
    console.log(`❌ Cannot connect to backend: ${error.message}`);
    console.log('Make sure your backend server is running on port 8080');
  }
}

async function checkMediumToken() {
  console.log('\n--- Checking Medium API Token ---');
  
  if (!MEDIUM_TOKEN) {
    console.log('❌ No Medium API token found for testing.');
    console.log('Please set the token directly in this script or as environment variable.');
    return;
  }
  
  // Only check if token exists, not its value
  console.log('✅ Medium API token is set');
}

async function runTests() {
  console.log('===============================================');
  console.log('          SCRIBLEY API TEST SCRIPT           ');
  console.log('===============================================');
  
  await checkBackendConnection();
  await checkMediumToken();
  
  console.log('\n--- Testing API Endpoints ---');
  
  // Test user endpoint
  await testEndpoint(`${API_BASE_URL}/users/me`, 'User info endpoint');
  
  // Test publications endpoint - add trailing slash
  await testEndpoint(`${API_BASE_URL}/publications/`, 'Publications endpoint');
  
  // Test articles endpoint - add trailing slash
  await testEndpoint(`${API_BASE_URL}/articles/`, 'Articles endpoint');
  
  console.log('\n===============================================');
  console.log('           TEST SCRIPT COMPLETED              ');
  console.log('===============================================');
}

runTests(); 