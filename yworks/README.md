# yWorks Neo4j Integration for Streamlit

This directory provides a working integration of yFiles for HTML with Streamlit for Neo4j graph visualization, specifically designed to work with the Neo4j Text2Cypher Agent workflow.

## The Problem

yFiles uses ES6 modules (`import`/`export`) which require proper MIME types. Streamlit serves JS files as `text/plain` for security, causing module loading to fail.

## The Solution: Bundle Approach

Convert yFiles ES6 modules into a single bundled JavaScript file that doesn't use modules.

```
yFiles ES6 Modules → Bundler → Single IIFE Bundle → Works in Streamlit!
```

## Directory Structure

```
yworks/
├── lib/                         # Your yFiles library files (REPLACE THESE)
│   ├── yfiles.js
│   ├── yfiles.css
│   └── impl/
├── dist/                        # Generated bundle (created after build)
│   ├── yfiles.bundle.js        # Single bundled file
│   └── yfiles.css
├── npm_build/                       # Build tools (self-contained)
│   ├── package.json            # Build configuration
│   ├── bundle.js               # Bundling script
│   └── node_modules/           # Build dependencies (created after npm install)
├── license.json                 # Your yFiles license (ADD YOUR LICENSE HERE)
├── streamlit_app.py            # Simple demo Streamlit app
├── streamlit_app_integrated.py # Neo4j workflow integration app (MAIN APP)
├── visualization.html          # yFiles visualization template
└── README.md                   # This file
```

## Complete Setup Guide

### Prerequisites
- Node.js and npm installed (for bundling)
- yFiles for HTML (evaluation or commercial license)
- Python with Poetry installed (for running the app)
- Neo4j database with credentials configured in `.env`

### 📋 Step-by-Step Instructions

#### Step 1: Prepare Your yFiles Library

1. **Navigate to the yworks directory:**
   ```bash
   cd neo4j-text2cypher-agent/yworks
   ```

2. **Replace the lib folder contents with your yFiles library:**
   ```bash
   # Remove existing placeholder files
   rm -rf lib/*
   
   # Copy your yFiles library files
   cp -r /path/to/your/yfiles-for-html/* ./lib/
   ```
   
   The `lib` folder should now contain:
   - `yfiles.js` (main library file)
   - `yfiles.css` (styles)
   - `impl/` directory (implementation files)
   - Other yFiles modules as needed

3. **Add your license file:**
   ```bash
   # Copy your yFiles license to the yworks directory
   cp /path/to/your/license.json ./license.json
   ```

#### Step 2: Build the Bundle

1. **Install build dependencies:**
   ```bash
   cd npm_build
   npm install
   ```

2. **Create the bundle:**
   ```bash
   npm run bundle
   ```
   
   This creates:
   - `dist/yfiles.bundle.js` - Single bundled JavaScript file
   - `dist/yfiles.css` - Copied CSS file

3. **Verify the bundle was created:**
   ```bash
   ls -la ../dist/
   # Should show yfiles.bundle.js and yfiles.css
   ```

#### Step 3: Run the Neo4j Integration App

1. **Navigate back to the project root:**
   ```bash
   cd ../..  # Back to neo4j-text2cypher-agent directory
   ```

2. **Ensure your Neo4j credentials are configured:**
   ```bash
   # Check that .env file exists with your Neo4j connection details
   cat .env
   ```

3. **Run the integrated app with Poetry:**
   ```bash
   poetry run streamlit run yworks/streamlit_app_integrated.py example_apps/iqs_data_explorer/app-config.yml
   ```

   Or if you want to test with a different config:
   ```bash
   poetry run streamlit run yworks/streamlit_app_integrated.py path/to/your/app-config.yml
   ```

### Quick Test

Once running, test with these example queries:
- **Your natural language:** Type any question about your data!

## How It Works

### The Bundle Process

1. **Input**: ES6 modules with `import`/`export`
   ```javascript
   // yfiles.js (ES6 modules)
   export * from './core.js'
   export * from './view.js'
   ```

2. **Bundler** (Vite/Rollup): Converts to IIFE
   ```javascript
   // yfiles.bundle.js (no modules!)
   (function() {
     // All code bundled here
     window.yfiles = { /* all exports */ };
   })();
   ```

3. **Usage**: Simple script tag
   ```html
   <script src="yfiles.bundle.js"></script>
   <script>
     // Use global yfiles variable
     const graph = new yfiles.view.GraphComponent();
   </script>
   ```

## Troubleshooting

### Bundle Not Found
- Run `cd npm_build && npm run bundle` first
- Check `dist/` directory exists

### yFiles Not Defined
- Check bundle was created successfully
- Verify global name in bundle script

### License Issues
- Ensure `license.json` is in the main yworks directory
- Check license expiration date

## Using Your Own Enterprise yFiles Templates

If you have existing yFiles enterprise templates, you only need **2 simple changes**:

### The 2 Required Changes:

1. **Replace import statements** with placeholders
2. **Add one function** to receive Neo4j data

That's it! Here's how:

#### 1. Replace Import Statements
Change these:
```html
<script src="lib/yfiles.js"></script>
<link rel="stylesheet" href="lib/yfiles.css">
```

To these placeholders:
```html
<script>{{BUNDLE_CONTENT}}</script>
<style>{{CSS_CONTENT}}</style>
```

#### 2. Add the Main Data Function
Add this function to receive and visualize Neo4j data:
```javascript
window.loadNeo4jData = function(data) {
    // data.nodes - Array of nodes from Neo4j
    // data.edges - Array of relationships
    
    // Your existing visualization code here
    // Use data.nodes and data.edges to build your graph
}
```

### Complete Example:

#### Custom Visualization Templates

To use your own visualization template:

1. **Create your HTML template** with these required elements:
   ```javascript
   window.loadNeo4jData = function(data) {
       // data.nodes - Array with {id, label, properties, labels, neo4j_id}
       // data.edges - Array with {source, target, type, properties}
   }
   ```

2. **Include placeholders**:
   - `{{BUNDLE_CONTENT}}` - Will be replaced with yFiles bundle
   - `{{CSS_CONTENT}}` - Will be replaced with CSS
   - `{{LICENSE_CONTENT}}` - Will be replaced with license

3. **Replace `visualization.html`** with your template having the same name

**Your Original Template:**
```html
<!DOCTYPE html>
<html>
<head>
    <script src="../../lib/yfiles.js"></script>
    <link rel="stylesheet" href="../../lib/yfiles.css">
</head>
<body>
    <div id="graphComponent"></div>
    <script>
        const graphComponent = new yfiles.view.GraphComponent('#graphComponent');
        // Your visualization logic
    </script>
</body>
</html>
```

**Modified for Neo4j Integration:**
```html
<!DOCTYPE html>
<html>
<head>
    <style>{{CSS_CONTENT}}</style>
</head>
<body>
    <div id="graphComponent"></div>
    <script>
        {{BUNDLE_CONTENT}}
        
        const graphComponent = new yfiles.view.GraphComponent('#graphComponent');
        // Your existing visualization logic
        
        // Add this function
        window.loadNeo4jData = function(data) {
            // Use your existing code with data.nodes and data.edges
        }
    </script>
</body>
</html>
```

## Neo4j Integration Architecture

### Data Flow
```
User Question → LangGraph Workflow → Neo4j Query → Result Object
                                                          ↓
                                                   result.graph()
                                                          ↓
                                              Nodes & Relationships
                                                          ↓
                                                  yFiles GraphBuilder
                                                          ↓
                                                   Visualization
```