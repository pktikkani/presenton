import { numberTranslations } from './others';

export function getNumberForLanguage(language: string, index: number): string {
  // First try exact match
  if (numberTranslations[language]) {
    return numberTranslations[language][index] || String(index + 1).padStart(2, '0');
  }
  
  // Normalize the language string
  const normalizedLang = language.trim().toLowerCase();
  
  // Try exact match with normalized keys
  const exactMatch = Object.keys(numberTranslations).find(key => 
    key.trim().toLowerCase() === normalizedLang
  );
  if (exactMatch && numberTranslations[exactMatch]) {
    return numberTranslations[exactMatch][index] || String(index + 1).padStart(2, '0');
  }
  
  // Try to find a language key that starts with the provided language
  const prefixMatch = Object.keys(numberTranslations).find(key => 
    key.toLowerCase().startsWith(normalizedLang)
  );
  if (prefixMatch && numberTranslations[prefixMatch]) {
    return numberTranslations[prefixMatch][index] || String(index + 1).padStart(2, '0');
  }
  
  // Try to match the language as a prefix (e.g., "Kannada" matches "Kannada (ಕನ್ನಡ)")
  const languageAsPrefix = Object.keys(numberTranslations).find(key => 
    normalizedLang.startsWith(key.toLowerCase().split(/[\s(]/)[0])
  );
  if (languageAsPrefix && numberTranslations[languageAsPrefix]) {
    return numberTranslations[languageAsPrefix][index] || String(index + 1).padStart(2, '0');
  }
  
  // Handle special cases
  const specialCases: { [key: string]: string } = {
    'english': 'English',
    'chinese': 'Chinese (Simplified & Traditional - 中文, 汉语/漢語)',
    'persian': 'Persian/Farsi (فارسی)',
    'farsi': 'Persian/Farsi (فارسی)',
    'irish': 'Irish (Gaeilge)',
    'scottish': 'Scottish Gaelic (Gàidhlig)',
    'tagalog': 'Tagalog/Filipino (Tagalog/Filipino)',
    'filipino': 'Tagalog/Filipino (Tagalog/Filipino)',
  };
  
  const specialMatch = specialCases[normalizedLang];
  if (specialMatch && numberTranslations[specialMatch]) {
    return numberTranslations[specialMatch][index] || String(index + 1).padStart(2, '0');
  }
  
  // Default to English format
  return String(index + 1).padStart(2, '0');
}