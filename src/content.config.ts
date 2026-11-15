import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Each project is one Markdown file in src/content/projects/.
// The file name is the page address, e.g. momo.md -> /momo
const projects = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/projects' }),
  schema: z.object({
    title: z.string(),
    eyebrow: z.string().default(''),     // small line above the title (school / client)
    summary: z.string(),
    team: z.string().optional(),
    tags: z.array(z.string()).default([]),
    hero: z.string().optional(),         // main image or video at the top of the page
    heroType: z.enum(['img', 'video']).default('img'),
    cover: z.string(),                   // image used on the home page grid
    cardLabel: z.string(),               // text shown on the grid card
    order: z.number(),                   // position in the "All projects" grid
    featured: z.number().optional(),     // position in the featured row at the top (leave out to hide)
  }),
});

export const collections = { projects };
