import { getHeader, getHeaderForFormData } from "./header";
import { IconSearch, ImageGenerate, ImageSearch } from "./params";

export class PresentationGenerationApi {

  static async getChapterDetails() {
    try {
      const response = await fetch(
        `/api/v2/ppt/chapter-details`,
        {
          method: "GET",
          headers: getHeader(),
          cache: "no-cache",
        }
      );
      if (response.status === 200) {
        const data = await response.json();
        return data;
      }
    } catch (error) {
      console.error("Error getting chapter details:", error);
      throw error;
    }
  }

  static async uploadDoc(documents: File[], images: File[]) {
    const formData = new FormData();

    documents.forEach((document) => {
      formData.append("documents", document);
    });

    images.forEach((image) => {
      formData.append("images", image);
    });

    try {
      const response = await fetch(
        `/api/v2/ppt/files/upload`,
        {
          method: "POST",
          headers: getHeaderForFormData(),
          // Remove Content-Type header as browser will set it automatically with boundary
          body: formData,
          cache: "no-cache",
        }
      );

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Upload error:", error);
      throw error;
    }
  }



  static async decomposeDocuments(documentKeys: string[], imageKeys: string[]) {
    try {
      const response = await fetch(
        `/api/v2/ppt/files/decompose`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify({
            documents: documentKeys,
            images: imageKeys,
          }),
          cache: "no-cache",
        }
      );
      if (response.status === 200) {
        const data = await response.json();

        return data;
      } else {
        throw new Error(`Failed to decompose files: ${response.statusText}`);
      }
    } catch (error) {
      console.error("Error in Decompose Files", error);
      throw error;
    }
  }
  static async titleGeneration({
    presentation_id,
  }: {
    presentation_id: string;
  }) {
    try {
      const response = await fetch(
        `/api/v2/ppt/outlines/generate`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify({
            prompt: prompt,
            presentation_id: presentation_id,
          }),
          cache: "no-cache",
        }
      );
      if (response.status === 200) {
        const data = await response.json();

        return data;
      } else {
        throw new Error(`Failed to generate titles: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in title generation", error);
      throw error;
    }
  }

  static async generatePresentation(presentationData: any) {
    try {
      // V2 endpoint: /api/v2/ppt/generate/presentation
      const response = await fetch(
        `/api/v2/ppt/generate/presentation`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify(presentationData),
          cache: "no-cache",
        }
      );
      if (response.status === 200) {
        const data = await response.json();
        
        // V2 returns a different structure, normalize it
        // V2 response: { id, title, slides, theme, message }
        // V1 expected: { presentation: {...}, slides: [...] }
        if (data.id && data.slides) {
          // Transform V2 response to match V1 format if needed
          return {
            presentation: {
              id: data.id,
              title: data.title,
              theme: data.theme,
              // Add any other fields the frontend expects
            },
            slides: data.slides,
            message: data.message || "Presentation generated successfully"
          };
        }
        
        return data;
      } else {
        throw new Error(
          `Failed to generate presentation: ${response.statusText}`
        );
      }
    } catch (error) {
      console.error("error in presentation generation", error);
      throw error;
    }
  }
  
  static async editSlide(
    presentation_id: string,
    index: number,
    prompt: string
  ) {
    try {
      const response = await fetch(
        `/api/v2/ppt/edit`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify({
            presentation_id,

            index,
            prompt,
          }),
          cache: "no-cache",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update slides");
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("error in slide update", error);
      throw error;
    }
  }

  static async updatePresentationContent(body: any) {
    try {
      const response = await fetch(
        `/api/v2/ppt/slides/update`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify(body),
          cache: "no-cache",
        }
      );
      if (response.ok) {
        const data = await response.json();

        return data;
      } else {
        throw new Error(
          `Failed to update presentation content: ${response.statusText}`
        );
      }
    } catch (error) {
      console.error("error in presentation content update", error);
      throw error;
    }
  }

  static async generateData(presentationData: any) {
    try {
      const response = await fetch(
        `/api/v2/ppt/generate/data`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify(presentationData),
          cache: "no-cache",
        }
      );
      if (response.ok) {
        const data = await response.json();

        return data;
      } else {
        throw new Error(`Failed to generate data: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in data generation", error);
      throw error;
    }
  }
  // IMAGE AND ICON SEARCH
  static async imageSearch(imageSearch: ImageSearch) {
    try {
      const response = await fetch(
        `/api/v2/ppt/image/search`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify(imageSearch),
          cache: "no-cache",
        }
      );
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error(`Failed to search images: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in image search", error);
      throw error;
    }
  }
  static async generateImage(imageGenerate: ImageGenerate) {
    try {
      const response = await fetch(
        `/api/v2/ppt/image/generate`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify(imageGenerate),
          cache: "no-cache",
        }
      );
      if (response.ok) {
        const data = await response.json();

        return data;
      } else {
        throw new Error(`Failed to generate images: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in image generation", error);
      throw error;
    }
  }
  static async searchIcons(iconSearch: IconSearch) {
    try {
      const response = await fetch(
        `/api/v2/ppt/icon/search`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify(iconSearch),
          cache: "no-cache",
        }
      );
      if (response.ok) {
        const data = await response.json();

        return data;
      } else {
        throw new Error(`Failed to search icons: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in icon search", error);
      throw error;
    }
  }

  static async updateDocuments(body: any) {
    try {
      const response = await fetch(
        `/api/v2/ppt/document/update`,
        {
          method: "POST",
          headers: getHeaderForFormData(),
          body: body,
          cache: "no-cache",
        }
      );
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error(`Failed to update documents: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in document update", error);
      throw error;
    }
  }

  // EXPORT PRESENTATION
  static async exportAsPPTX(presentationData: any) {
    try {
      const response = await fetch(
        `/api/v2/ppt/presentation/export_as_pptx`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify(presentationData),
          cache: "no-cache",
        }
      );
      if (response.ok) {
        return await response.json();
      } else {
        throw new Error(`Failed to export as pptx: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in pptx export", error);
      throw error;
    }
  }
  static async exportAsPDF(presentationData: any) {
    try {
      const response = await fetch(
        `/api/v2/ppt/presentation/export_as_pdf`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify(presentationData),
        }
      );
      if (response.ok) {
        const data = await response.json();

        return data;
      } else {
        throw new Error(`Failed to export as pdf: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in pdf export", error);
      throw error;
    }
  }
  static async deleteSlide(presentation_id: string, slide_id: string) {
    try {
      const response = await fetch(
        `/api/v2/ppt/slide/delete?presentation_id=${presentation_id}&slide_id=${slide_id}`,
        {
          method: "DELETE",
          headers: getHeader(),
          cache: "no-cache",
        }
      );
      if (response.status === 204) {
        return true;
      } else {
        throw new Error(`Failed to delete slide: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in slide deletion", error);
      throw error;
    }
  }
  // SET THEME COLORS
  static async setThemeColors(presentation_id: string, theme: any) {
    try {
      const response = await fetch(
        `/api/v2/ppt/presentation/theme`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify({
            presentation_id,
            theme,
          }),

        }
      );
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error(`Failed to set theme colors: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in theme colors set", error);
      throw error;
    }
  }
  // QUESTIONS

  static async getQuestions({
    prompt,
    n_slides,
    documents,
    images,
    language,
    slide_mode,
    model,
  }: {
    prompt: string;
    n_slides: number | null;
    documents?: string[];
    images?: string[];
    language: string | null;
    slide_mode?: string;
    model?: string;
  }) {
    try {
      const response = await fetch(
        `/api/v2/ppt/create`,
        {
          method: "POST",
          headers: getHeader(),
          body: JSON.stringify({
            prompt,
            n_slides,
            language,
            documents,
            images,
            slide_mode,
            model, // V2 supports model parameter
          }),
          cache: "no-cache",
        }
      );
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error(`Failed to get questions: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in question generation", error);
      throw error;
    }
  }
  
  // New V2 specific method to get available models
  static async getAvailableModels() {
    try {
      const response = await fetch(
        `/api/v2/ppt/models`,
        {
          method: "GET",
          headers: getHeader(),
          cache: "no-cache",
        }
      );
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error(`Failed to get available models: ${response.statusText}`);
      }
    } catch (error) {
      console.error("error in getting models", error);
      throw error;
    }
  }
}