<template>
   <footer class="app-footer">
      <div class="footer-links">
         <a href="https://www.elex.is">About ELEXIS</a>
         <RouterLink :to="{ name: 'docs-intro' }">Help</RouterLink>
         <a href="mailto:info@elex.is">Contact us</a>
      </div>
      <div class="footer-logos">
         <div class="funding">
            <a href="https://www.elex.is/" target="_blank" aria-label="ELEXIS">
               <span class="elexislogo" aria-hidden="true"/>
            </a>
            <span class="horizon-info">
               <span class="eulogo" aria-hidden="true"/>
               This project has received funding from the European Union's Horizon 2020<br>
               research and innovation programme under grant agreement No 731015.
            </span>
         </div>
         <div class="version right">
            <span>Version:<br>{{ version }}</span>
            <a href="https://github.com/elexis-eu/lexonomy" target="_blank" aria-label="Lexonomy on GitHub">
               <span class="githublogo" aria-hidden="true"/>
            </a>
         </div>
      </div>
   </footer>
</template>

<script setup lang="ts">
const version = import.meta.env.VITE_LEXONOMY_VERSION || 'dev'
</script>

<style>
.app-footer .footer-links {
   text-align: right;
   padding: 0 20px 10px 0;
}
.app-footer .footer-links a {
   color: #004494;
   font-size: 14px;
   line-height: 18px;
   margin-left: 30px;
}
.app-footer .footer-logos {
   padding: 15px 20px 50px 50px;
   background: #f0f8ff;
   border-top: 1px solid #004494;
}
.app-footer .funding a {
   display: inline-block;
   height: 30px;
   vertical-align: middle;
}
.app-footer .funding a::after {
   display: inline-block;
   height: 30px;
   margin: 0 10px;
   border-right: 1px solid #fff;
   content: " ";
}
.app-footer .version {
   font-weight: 100;
   color: #004494;
   font-size: x-small;
   line-height: 1.5em;
   text-align: right;
   position: relative;
   top: -20px;
}
.app-footer .version > span {
   display: inline-block;
}
.app-footer .version a {
   margin-left: 5px;
}
.app-footer .horizon-info {
   height: 30px;
   display: inline-block;
   vertical-align: middle;
   color: #004494;
   font-size: x-small;
   line-height: 1.5em;
}
.app-footer .elexislogo,
.app-footer .eulogo,
.app-footer .githublogo {
   display: inline-block;
   background-size: contain;
   background-repeat: no-repeat;
}
.app-footer .elexislogo {
   width: 112px;
   height: 30px;
   background-image: url(/assets/img/logo_elexis.png);
}
.app-footer .eulogo {
   width: 45px;
   height: 30px;
   background-image: url(/assets/img/logo_eu.png);
   float: left;
   margin-right: 5px;
}
.app-footer .githublogo {
   width: 20px;
   height: 20px;
   background-image: url(/assets/img/github.png);
}
</style>
