#!/usr/bin/env node
/**
 * Bundle yFiles ES6 modules into a single IIFE file that works with Streamlit
 * This creates a global 'yfiles' variable with proper namespaces like yfiles.view, yfiles.geometry, etc.
 */

import { build } from 'vite';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';

const __dirname = dirname(fileURLToPath(import.meta.url));

async function bundleYFiles() {
  console.log('📦 Bundling yFiles library with nested structure...');
  
  try {
    // Use Vite to bundle into IIFE format
    await build({
      configFile: false,
      build: {
        lib: {
          entry: resolve(__dirname, '../lib/yfiles.js'),
          name: 'yfilesExports',
          formats: ['iife'],
          fileName: () => 'yfiles.temp.js'
        },
        outDir: resolve(__dirname, '../dist'),
        emptyOutDir: false,
        rollupOptions: {
          output: {
            extend: false,
            assetFileNames: '[name][extname]'
          }
        }
      }
    });

    // Read the temporary bundled file
    const tempBundle = await fs.readFile(
      resolve(__dirname, '../dist/yfiles.temp.js'),
      'utf-8'
    );

    // Create the final wrapper with nested structure
    const wrapperCode = `
(function(global) {
  'use strict';
  
  // yFiles bundled code wrapped to create proper namespace structure
  var yfilesExports;
  
  // Execute the bundled code to get all exports
  ${tempBundle.replace('var yfilesExports =', 'yfilesExports =')}
  
  // Create the yfiles namespace object with proper structure
  var yfiles = {
    // Create namespace objects
    lang: {},
    view: {},
    geometry: {},
    layout: {},
    graph: {},
    graphml: {},
    algorithms: {},
    collections: {},
    router: {},
    styles: {}
  };
  
  // Map exports to their proper namespaces
  // This recreates the standard yFiles API structure
  
  // Core lang exports
  if (yfilesExports.License) yfiles.License = yfilesExports.License;
  if (yfilesExports.Class) yfiles.Class = yfilesExports.Class;
  if (yfilesExports.Enum) yfiles.Enum = yfilesExports.Enum;
  if (yfilesExports.Interface) yfiles.Interface = yfilesExports.Interface;
  if (yfilesExports.BaseClass) yfiles.BaseClass = yfilesExports.BaseClass;
  if (yfilesExports.Exception) yfiles.Exception = yfilesExports.Exception;
  if (yfilesExports.delegate) yfiles.delegate = yfilesExports.delegate;
  
  // View namespace - common classes
  if (yfilesExports.GraphComponent) yfiles.view.GraphComponent = yfilesExports.GraphComponent;
  if (yfilesExports.GraphEditorInputMode) yfiles.view.GraphEditorInputMode = yfilesExports.GraphEditorInputMode;
  if (yfilesExports.GraphViewerInputMode) yfiles.view.GraphViewerInputMode = yfilesExports.GraphViewerInputMode;
  if (yfilesExports.DefaultLabelStyle) yfiles.view.DefaultLabelStyle = yfilesExports.DefaultLabelStyle;
  if (yfilesExports.ShapeNodeStyle) yfiles.view.ShapeNodeStyle = yfilesExports.ShapeNodeStyle;
  if (yfilesExports.PolylineEdgeStyle) yfiles.view.PolylineEdgeStyle = yfilesExports.PolylineEdgeStyle;
  if (yfilesExports.Arrow) yfiles.view.Arrow = yfilesExports.Arrow;
  if (yfilesExports.Color) yfiles.view.Color = yfilesExports.Color;
  if (yfilesExports.Fill) yfiles.view.Fill = yfilesExports.Fill;
  if (yfilesExports.Stroke) yfiles.view.Stroke = yfilesExports.Stroke;
  if (yfilesExports.SolidColorFill) yfiles.view.SolidColorFill = yfilesExports.SolidColorFill;
  if (yfilesExports.Font) yfiles.view.Font = yfilesExports.Font;
  
  // Geometry namespace  
  if (yfilesExports.Rect) yfiles.geometry.Rect = yfilesExports.Rect;
  if (yfilesExports.Point) yfiles.geometry.Point = yfilesExports.Point;
  if (yfilesExports.Size) yfiles.geometry.Size = yfilesExports.Size;
  if (yfilesExports.Insets) yfiles.geometry.Insets = yfilesExports.Insets;
  if (yfilesExports.Matrix) yfiles.geometry.Matrix = yfilesExports.Matrix;
  if (yfilesExports.GeneralPath) yfiles.geometry.GeneralPath = yfilesExports.GeneralPath;
  
  // Graph namespace
  if (yfilesExports.DefaultGraph) yfiles.graph.DefaultGraph = yfilesExports.DefaultGraph;
  if (yfilesExports.GraphBuilder) yfiles.graph.GraphBuilder = yfilesExports.GraphBuilder;
  if (yfilesExports.IGraph) yfiles.graph.IGraph = yfilesExports.IGraph;
  if (yfilesExports.INode) yfiles.graph.INode = yfilesExports.INode;
  if (yfilesExports.IEdge) yfiles.graph.IEdge = yfilesExports.IEdge;
  if (yfilesExports.ILabel) yfiles.graph.ILabel = yfilesExports.ILabel;
  if (yfilesExports.IPort) yfiles.graph.IPort = yfilesExports.IPort;
  
  // Layout namespace
  if (yfilesExports.HierarchicLayout) yfiles.layout.HierarchicLayout = yfilesExports.HierarchicLayout;
  if (yfilesExports.OrganicLayout) yfiles.layout.OrganicLayout = yfilesExports.OrganicLayout;
  if (yfilesExports.CircularLayout) yfiles.layout.CircularLayout = yfilesExports.CircularLayout;
  if (yfilesExports.TreeLayout) yfiles.layout.TreeLayout = yfilesExports.TreeLayout;
  if (yfilesExports.RadialLayout) yfiles.layout.RadialLayout = yfilesExports.RadialLayout;
  if (yfilesExports.OrthogonalLayout) yfiles.layout.OrthogonalLayout = yfilesExports.OrthogonalLayout;
  if (yfilesExports.LayoutExecutor) yfiles.layout.LayoutExecutor = yfilesExports.LayoutExecutor;
  
  // GraphML namespace
  if (yfilesExports.GraphMLSupport) yfiles.graphml.GraphMLSupport = yfilesExports.GraphMLSupport;
  if (yfilesExports.GraphMLIOHandler) yfiles.graphml.GraphMLIOHandler = yfilesExports.GraphMLIOHandler;
  
  // Collections namespace
  if (yfilesExports.List) yfiles.collections.List = yfilesExports.List;
  if (yfilesExports.Map) yfiles.collections.Map = yfilesExports.Map;
  if (yfilesExports.IEnumerable) yfiles.collections.IEnumerable = yfilesExports.IEnumerable;
  
  // Router namespace  
  if (yfilesExports.EdgeRouter) yfiles.router.EdgeRouter = yfilesExports.EdgeRouter;
  if (yfilesExports.PolylineEdgeRouter) yfiles.router.PolylineEdgeRouter = yfilesExports.PolylineEdgeRouter;
  
  // Add all other exports to maintain full compatibility
  // This ensures nothing is missed
  for (var key in yfilesExports) {
    if (yfilesExports.hasOwnProperty(key) && !yfiles[key]) {
      // Add to root if not already mapped
      yfiles[key] = yfilesExports[key];
    }
  }
  
  // Make yfiles available globally
  global.yfiles = yfiles;
  
})(typeof window !== 'undefined' ? window : this);
`;

    // Write the final bundled file
    await fs.writeFile(
      resolve(__dirname, '../dist/yfiles.bundle.js'),
      wrapperCode,
      'utf-8'
    );

    // Remove temporary file
    await fs.unlink(resolve(__dirname, '../dist/yfiles.temp.js'));

    // Copy CSS file
    try {
      await fs.copyFile(
        resolve(__dirname, '../lib/yfiles.css'),
        resolve(__dirname, '../dist/yfiles.css')
      );
      console.log('✅ CSS file copied');
    } catch (e) {
      console.log('⚠️ No CSS file to copy');
    }

    console.log('✅ Bundle created at dist/yfiles.bundle.js');
    console.log('📝 The bundle preserves the nested structure:');
    console.log('   - yfiles.view.GraphComponent');
    console.log('   - yfiles.geometry.Rect');
    console.log('   - yfiles.License.value = {...}');
    console.log('\n💡 Users can use standard yFiles API without any changes!');
    
  } catch (error) {
    console.error('❌ Error bundling:', error);
    process.exit(1);
  }
}

bundleYFiles();