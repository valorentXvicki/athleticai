from transformers import pipeline

class EventRecommender:
    def __init__(self):
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.candidate_labels = ["marathon", "running", "trail", "club", "beginner", "community"]

    def score_events(self, events, interests):
        results = []
        for event in events:
            pred = self.classifier(event["name"], self.candidate_labels)
            matches = {label: score for label, score in zip(pred["labels"], pred["scores"]) if label in interests}
            if matches:
                best_label = max(matches, key=lambda x: matches[x])
                event["tag"] = best_label
                event["score"] = matches[best_label]
                results.append(event)
        return sorted(results, key=lambda x: x["score"], reverse=True)