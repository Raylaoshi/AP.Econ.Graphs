// /lib/graph-common.js

(function() {
    // 1. Settings
    // Use the absolute URL so this script works from any sub-folder depth
    const basePath = "https://raylaoshi.github.io/AP.Econ.Graphs/lib/";

    // Helper function to append elements to <head> safely
    const head = document.head || document.getElementsByTagName('head')[0];

    // 2. Inject Custom CSS 
    // We inject this *first* and *synchronously* to ensure the raw YAML text 
    // is hidden before the body renders.
    const customStyle = document.createElement('style');
    customStyle.textContent = `
        /* Hide the raw YAML text */
        .kg-container { 
            visibility: hidden; 
            position: relative; 
            min-height: 500px; /* Reserve space so layout doesn't jump */
        }
        /* Make the graph visible once the engine draws it */
        .kg-container svg { 
            visibility: visible; 
            position: absolute;
            top: 0; 
            left: 0;
        }
        /* Prevent selecting text inside the graph (drag fix) */
        svg text { pointer-events: none; }
    `;
    head.appendChild(customStyle);

    // 3. Inject the KGJS CSS file
    const kgLink = document.createElement('link');
    kgLink.rel = 'stylesheet';
    kgLink.type = 'text/css';
    kgLink.href = basePath + 'kg.0.4.0.css';
    head.appendChild(kgLink);

    // 4. Inject the KGJS Library Script
    const kgScript = document.createElement('script');
    kgScript.src = basePath + 'kg.0.4.0.js';
    // 'async = false' ensures it executes in order if you add more scripts later
    kgScript.async = false; 
    head.appendChild(kgScript);

    // 5. Add Global Event Listeners
    // This runs after the HTML is fully parsed
    document.addEventListener('DOMContentLoaded', function() {
        const container = document.querySelector('.kg-container');
        if (container) {
            // Prevent dragging the whole SVG when trying to drag graph elements
            container.addEventListener('mousedown', function(e) {
                if (e.target.closest('svg')) {
                    e.preventDefault();
                }
            }, true);
        }
    });

})();