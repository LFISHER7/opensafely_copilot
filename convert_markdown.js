const fs = require('fs-extra');
const path = require('path');
const MarkdownIt = require('markdown-it');
const md = new MarkdownIt();

/**
 * Reads a markdown file and converts each section to plain text.
 * @param {string} filePath - Path to the markdown file.
 * @returns {Array<{ header: string, plainText: string }>} An array of section objects containing header and plain text.
 */
async function convertMarkdownToText(filePath) {
  try {
    const markdownContent = await fs.readFile(filePath, 'utf-8');

    // Split markdown content into sections based on headers
    const sections = markdownContent.split(/(?=^#{1,2}\s)/gm);
    const sectionData = sections.map((section) => {
      const headerMatch = section.match(/^#{1,6}\s(.*)$/m);
      const header = headerMatch ? headerMatch[1] : 'no_header';
      const htmlContent = md.render(section);
      const plainText = htmlContent.replace(/<\/?[^>]+(>|$)/g, '');
      return { header, plainText };
    });
    return sectionData;
  } catch (error) {
    console.error('Error reading file:', error);
  }
}

/**
 * Main function that converts all markdown files in the input directory to plain text files in the output directory.
 * @param {string} inputDir - Path to the input directory containing markdown files.
 * @param {string} outputDir - Path to the output directory where plain text files will be written.
 */
async function main(inputDir, outputDir) {
  // Ensure output directory exists
  await fs.ensureDir(outputDir);

  try {
    // Get list of markdown files in input directory
    const files = await fs.readdir(inputDir);
    const mdFiles = files.filter((file) => path.extname(file) === '.md');

    // Loop through markdown files
    for (const mdFile of mdFiles) {
      const inputFilePath = path.join(inputDir, mdFile);
      const sectionData = await convertMarkdownToText(inputFilePath);

      // Write plain text sections to output directory
      sectionData.forEach(async ({ header, plainText }) => {
        const sanitizedHeader = header
          ? header.replace(/[^a-zA-Z0-9-_]/g, '-')
          : 'no_header';
        const outputFileName =
          path.basename(mdFile, '.md') + `_section_${sanitizedHeader}.txt`;
        const outputFilePath = path.join(outputDir, outputFileName);

        await fs.writeFile(outputFilePath, plainText);
        console.log(`Converted ${mdFile} to ${outputFileName}`);
      });
    }
  } catch (error) {
    console.error('Error processing files:', error);
  }
}

// Run main function with default input and output directories
main('copilot/data/data/', 'copilot/data/doc-sections')