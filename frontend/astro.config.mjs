// astro.config.mjs
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite'; // usar tailwindcss en la pagina
import icon from 'astro-icon'; // poder usar iconos en los componentes

export default defineConfig({
  integrations: [
    icon()  // poder usar iconos en los componentes
  ],
  vite: {
    plugins: [tailwindcss()], // usar tailwindcss en la pagina
  },
});
