.. _sensors:

Sensors
=======

Camera modules and sensor adapters that connect to the FPC connector
on supported OpenMV Cams. Each page covers the sensor's resolution,
pixel format, supported frame sizes, and the MicroPython API for
driving it.

.. raw:: html

   <div class="omv-cards-page">
     <section class="omv-section">
       <div class="omv-grid cols-3">

         <a class="omv-card module icon-blue" href="sensors/ov5640.html">
           <div class="omv-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg></div>
           <h4>OV5640</h4>
           <p>5-MP rolling-shutter colour sensor with autofocus support.</p>
           <span class="card-arrow">Explore →</span>
         </a>

         <a class="omv-card module icon-purple" href="sensors/ps5520.html">
           <div class="omv-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/><path d="M9 13l2 2 4-4"/></svg></div>
           <h4>PS5520</h4>
           <p>5-MP HDR sensor with high dynamic range — challenging-light scenes.</p>
           <span class="card-arrow">Explore →</span>
         </a>

         <a class="omv-card module icon-green" href="sensors/mt9v024.html">
           <div class="omv-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M3 9l3-3M21 9l-3-3"/></svg></div>
           <h4>MT9V024</h4>
           <p>Global-shutter monochrome sensor — high-speed capture without rolling-shutter artifacts.</p>
           <span class="card-arrow">Explore →</span>
         </a>

         <a class="omv-card module icon-amber" href="sensors/pag7936.html">
           <div class="omv-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><circle cx="12" cy="14" r="3"/></svg></div>
           <h4>PAG7936 Multispectral Thermal</h4>
           <p>1-MP global-shutter multispectral thermal module — OpenMV N6 only.</p>
           <span class="card-arrow">Explore →</span>
         </a>

         <a class="omv-card module icon-coral" href="sensors/genx320.html">
           <div class="omv-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg></div>
           <h4>GENX320 Event Camera</h4>
           <p>Prophesee event-based vision sensor — microsecond temporal resolution.</p>
           <span class="card-arrow">Explore →</span>
         </a>

         <a class="omv-card module icon-purple" href="sensors/multispectral-event.html">
           <div class="omv-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/><circle cx="12" cy="12" r="3"/></svg></div>
           <h4>Multispectral Event Camera</h4>
           <p>Combined multispectral and event-based sensor module.</p>
           <span class="card-arrow">Explore →</span>
         </a>

         <a class="omv-card module icon-amber" href="sensors/flir-lepton.html">
           <div class="omv-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></div>
           <h4>FLIR Lepton Adapter</h4>
           <p>Adapter for FLIR Lepton thermal modules — 80×60 to 160×120 thermal.</p>
           <span class="card-arrow">Explore →</span>
         </a>

         <a class="omv-card module icon-amber" href="sensors/flir-boson.html">
           <div class="omv-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="14" y2="9"/></svg></div>
           <h4>FLIR Boson Adapter</h4>
           <p>Adapter for FLIR Boson thermal modules — higher-resolution thermal imaging.</p>
           <span class="card-arrow">Explore →</span>
         </a>

       </div>
     </section>
   </div>

.. toctree::
   :hidden:

   sensors/ov5640.rst
   sensors/ps5520.rst
   sensors/mt9v024.rst
   sensors/pag7936.rst
   sensors/genx320.rst
   sensors/multispectral-event.rst
   sensors/flir-lepton.rst
   sensors/flir-boson.rst
