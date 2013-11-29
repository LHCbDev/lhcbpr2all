function(doc) {
  var job;
  if (doc.type == "build-result" || doc.type == "tests-result") {
    if (doc.type == "build-result") {
      job = "build";
    } else {
      job = "tests";
    }
    emit(doc.started,
         {event: "started",
          job: job,
          slot: doc.slot,
          build_id: doc.build_id,
          platform: doc.platform
         });
    emit(doc.completed,
         {event: "completed",
          job: job,
          slot: doc.slot,
          build_id: doc.build_id,
          platform: doc.platform
         });
  }
}
