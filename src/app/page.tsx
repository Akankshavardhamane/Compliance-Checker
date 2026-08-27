"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UploadCloud, Loader2 } from "lucide-react";
import { uploadLabel } from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsProcessing(true);
    try {
      const result = await uploadLabel(file);
      router.push(`/results/${result.scan_id}`);
    } catch (error) {
      console.error(error);
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Product Label</h1>
        <p className="text-gray-500 mb-8">
          Upload an image of the packaged product's label to analyze its compliance with Legal Metrology Rules.
        </p>

        {!preview ? (
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 hover:bg-gray-50 transition-colors">
            <input
              type="file"
              id="label-upload"
              className="hidden"
              accept="image/*"
              onChange={handleFileChange}
            />
            <label htmlFor="label-upload" className="cursor-pointer flex flex-col items-center">
              <div className="bg-blue-50 p-4 rounded-full mb-4">
                <UploadCloud className="h-8 w-8 text-blue-600" />
              </div>
              <span className="text-lg font-medium text-gray-900">Click to upload</span>
              <span className="text-sm text-gray-500 mt-1">or drag and drop</span>
              <span className="text-xs text-gray-400 mt-2">SVG, PNG, JPG or GIF (max. 10MB)</span>
            </label>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="relative w-64 h-64 mb-6 rounded-lg overflow-hidden border border-gray-200">
              <img src={preview} alt="Label Preview" className="object-cover w-full h-full" />
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => {
                  setFile(null);
                  setPreview(null);
                }}
                disabled={isProcessing}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                Clear
              </button>
              <button
                onClick={handleAnalyze}
                disabled={isProcessing}
                className="flex items-center gap-2 px-6 py-2 bg-black text-white rounded-md font-medium hover:bg-gray-800 disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Analyze Label"
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
